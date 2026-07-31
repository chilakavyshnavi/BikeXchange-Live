"""
URL configuration for the auctions app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'auctions'

router = DefaultRouter()
router.register(r'admin', views.AdminAuctionViewSet, basename='admin-auction')

urlpatterns = [
    # Public auction endpoints
    path('', views.AuctionViewSet.as_view({'get': 'list'}), name='auction-list'),
    path('<uuid:pk>/', views.AuctionViewSet.as_view({'get': 'retrieve'}), name='auction-detail'),

    # Bid endpoints
    path('<uuid:auction_id>/bids/', views.BidListCreateView.as_view(), name='bid-list-create'),

    # User's bids
    path('my-bids/', views.UserBidsView.as_view(), name='user-bids'),

    # Admin auction management (includes create, update, delete, cancel)
    path('', include(router.urls)),
]
