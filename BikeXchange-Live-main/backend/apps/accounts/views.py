"""
Authentication and user profile API views.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Returns JWT tokens upon successful registration.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f'New user registered: {user.email} (role={user.role})')

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Registration successful.',
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView):
    """
    Authenticate user and return JWT tokens.
    
    Use email and password to obtain access and refresh tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Enrich response with user data
            email = request.data.get('email', '')
            try:
                user = User.objects.get(email=email)
                response.data['user'] = UserSerializer(user).data
                logger.info(f'User logged in: {email}')
            except User.DoesNotExist:
                pass

        return response


@extend_schema(tags=['Auth'])
class RefreshTokenView(TokenRefreshView):
    """Refresh an access token using a valid refresh token."""
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Auth'])
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the authenticated user's profile.
    
    GET: Returns current user profile with bid statistics.
    PUT/PATCH: Updates user profile fields.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=['Admin'])
class UserListView(generics.ListAPIView):
    """
    List all users (admin only).
    
    Returns paginated list of all registered users.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        return User.objects.all().order_by('-created_at')


@extend_schema(tags=['Admin'])
class DashboardStatsView(APIView):
    """
    Admin dashboard statistics.
    
    Returns aggregated platform statistics including
    user counts, auction metrics, and bid activity.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {'detail': 'Admin access required.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.auctions.models import Auction, Bid  # type: ignore

        total_users = User.objects.count()
        total_auctions = Auction.objects.count()
        active_auctions = Auction.objects.filter(status=Auction.Status.ACTIVE).count()
        completed_auctions = Auction.objects.filter(status=Auction.Status.COMPLETED).count()
        total_bids = Bid.objects.count()

        # Calculate total revenue (sum of winning bids)
        from django.db.models import Sum
        total_revenue = Auction.objects.filter(
            status=Auction.Status.COMPLETED,
            winner__isnull=False,
        ).aggregate(total=Sum('current_price'))['total'] or 0

        return Response({
            'total_users': total_users,
            'total_auctions': total_auctions,
            'active_auctions': active_auctions,
            'completed_auctions': completed_auctions,
            'total_bids': total_bids,
            'total_revenue': float(total_revenue),
        })
