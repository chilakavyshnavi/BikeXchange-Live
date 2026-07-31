"""
API views for auction browsing, management, and bid placement.
"""

import logging

from django.db.models import Q, Count
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.core.permissions import IsAdminUser
from .models import Auction, Bid, Bike
from .serializers import (
    AuctionListSerializer,
    AuctionDetailSerializer,
    CreateAuctionSerializer,
    BidSerializer,
    PlaceBidSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=['Auctions'])
@extend_schema_view(
    list=extend_schema(
        summary='List all auctions',
        description='Browse auctions with optional filtering by status, make, and search.',
        parameters=[
            OpenApiParameter('status', str, description='Filter by status: SCHEDULED, ACTIVE, COMPLETED, CANCELLED'),
            OpenApiParameter('make', str, description='Filter by bike make (e.g., "Royal Enfield")'),
            OpenApiParameter('search', str, description='Search auction titles and bike make/model'),
            OpenApiParameter('ordering', str, description='Order by: created_at, current_price, end_time, -created_at, -current_price'),
        ],
    ),
    retrieve=extend_schema(
        summary='Get auction details',
        description='Full auction details including bike info, bid history, and countdown.',
    ),
)
class AuctionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public auction browsing endpoints.
    
    Supports filtering by status, bike make, search, and ordering.
    Uses different serializers for list vs detail views.
    """
    queryset = Auction.objects.select_related('bike', 'seller', 'winner').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'bike__make', 'bike__model', 'description']
    ordering_fields = ['created_at', 'current_price', 'end_time', 'start_time']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AuctionDetailSerializer
        return AuctionListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())

        # Filter by bike make
        make = self.request.query_params.get('make')
        if make:
            qs = qs.filter(bike__make__icontains=make)

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(current_price__gte=min_price)
        if max_price:
            qs = qs.filter(current_price__lte=max_price)

        return qs


@extend_schema(tags=['Admin'])
class AdminAuctionViewSet(viewsets.ModelViewSet):
    """
    Admin auction management endpoints.
    
    Full CRUD for auctions. Only accessible by admin users.
    Creating an auction also creates the associated bike.
    """
    queryset = Auction.objects.select_related('bike', 'seller', 'winner').all()
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create']:
            return CreateAuctionSerializer
        if self.action in ['retrieve']:
            return AuctionDetailSerializer
        return AuctionListSerializer

    def perform_create(self, serializer):
        auction = serializer.save()
        logger.info(
            f'Auction created: {auction.title} (id={auction.id}) '
            f'by {self.request.user.email}'
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled or active auction."""
        auction = self.get_object()
        if auction.status in [Auction.Status.COMPLETED, Auction.Status.CANCELLED]:
            return Response(
                {'detail': 'Cannot cancel a completed or already cancelled auction.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auction.status = Auction.Status.CANCELLED
        auction.save(update_fields=['status', 'updated_at'])
        logger.info(f'Auction cancelled: {auction.title} (id={auction.id})')

        return Response({'detail': 'Auction cancelled successfully.'})


@extend_schema(tags=['Bids'])
class BidListCreateView(generics.ListCreateAPIView):
    """
    List bids for an auction or place a new bid.
    
    GET: Returns paginated bid history for the specified auction.
    POST: Places a new bid (must be authenticated, amount validated).
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PlaceBidSerializer
        return BidSerializer

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        return Bid.objects.filter(
            auction_id=auction_id
        ).select_related('bidder').order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            try:
                context['auction'] = Auction.objects.get(pk=self.kwargs['auction_id'])
            except Auction.DoesNotExist:
                pass
        return context

    def create(self, request, *args, **kwargs):
        try:
            auction = Auction.objects.get(pk=self.kwargs['auction_id'])
        except Auction.DoesNotExist:
            return Response(
                {'detail': 'Auction not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bid = serializer.save()

        logger.info(
            f'Bid placed: ₹{bid.amount:,.2f} on "{auction.title}" '
            f'by {request.user.email}'
        )

        # Return the created bid with bidder info
        return Response(
            BidSerializer(bid).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Auctions'])
class UserBidsView(generics.ListAPIView):
    """List all bids placed by the authenticated user."""

    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.filter(
            bidder=self.request.user
        ).select_related('auction', 'bidder').order_by('-created_at')
