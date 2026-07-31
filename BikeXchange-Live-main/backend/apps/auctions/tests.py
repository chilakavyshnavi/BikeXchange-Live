"""
Tests for the auctions app — auction CRUD, bidding, lifecycle.
"""

import pytest
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.auctions.models import Bike, Auction, Bid

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email='admin@test.com',
        username='admin',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User',
        role='ADMIN',
        is_staff=True,
    )


@pytest.fixture
def buyer_user():
    return User.objects.create_user(
        email='buyer@test.com',
        username='buyer',
        password='BuyerPass123!',
        first_name='Buyer',
        last_name='User',
        role='BUYER',
    )


@pytest.fixture
def buyer2_user():
    return User.objects.create_user(
        email='buyer2@test.com',
        username='buyer2',
        password='BuyerPass123!',
        first_name='Buyer2',
        last_name='User',
        role='BUYER',
    )


@pytest.fixture
def sample_bike():
    return Bike.objects.create(
        make='Royal Enfield',
        model='Classic 350',
        year=2022,
        mileage=12000,
        engine_cc=349,
        fuel_type='PETROL',
        color='Black',
        condition='EXCELLENT',
        description='Test bike',
        images=[],
    )


@pytest.fixture
def active_auction(sample_bike, admin_user):
    now = timezone.now()
    return Auction.objects.create(
        title='Test Active Auction',
        description='A test auction',
        bike=sample_bike,
        seller=admin_user,
        start_price=Decimal('100000'),
        current_price=Decimal('100000'),
        min_increment=Decimal('1000'),
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=5),
        status='ACTIVE',
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def buyer_client(api_client, buyer_user):
    api_client.force_authenticate(user=buyer_user)
    return api_client


@pytest.mark.django_db
class TestAuctionList:
    """Tests for auction listing and filtering."""

    def test_list_auctions(self, api_client, active_auction):
        response = api_client.get('/api/auctions/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_filter_by_status(self, api_client, active_auction):
        response = api_client.get('/api/auctions/?status=ACTIVE')
        assert response.status_code == status.HTTP_200_OK
        for auction in response.data['results']:
            assert auction['status'] == 'ACTIVE'

    def test_auction_detail(self, api_client, active_auction):
        response = api_client.get(f'/api/auctions/{active_auction.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Active Auction'
        assert 'bike' in response.data
        assert 'bids' in response.data


@pytest.mark.django_db
class TestAuctionAdmin:
    """Tests for admin auction management."""

    def test_create_auction_as_admin(self, admin_client):
        now = timezone.now()
        data = {
            'title': 'New Auction',
            'description': 'Test auction',
            'start_price': 50000,
            'min_increment': 500,
            'start_time': (now + timedelta(hours=1)).isoformat(),
            'end_time': (now + timedelta(hours=12)).isoformat(),
            'bike_make': 'Honda',
            'bike_model': 'CB300R',
            'bike_year': 2023,
            'bike_mileage': 5000,
            'bike_engine_cc': 286,
            'bike_fuel_type': 'PETROL',
            'bike_color': 'Silver',
            'bike_condition': 'EXCELLENT',
        }
        response = admin_client.post('/api/auctions/admin/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_auction_as_buyer_forbidden(self, buyer_client):
        now = timezone.now()
        data = {
            'title': 'Unauthorized Auction',
            'description': 'Should fail',
            'start_price': 50000,
            'min_increment': 500,
            'start_time': (now + timedelta(hours=1)).isoformat(),
            'end_time': (now + timedelta(hours=12)).isoformat(),
            'bike_make': 'Test',
            'bike_model': 'Test',
            'bike_year': 2023,
            'bike_mileage': 1000,
            'bike_engine_cc': 150,
            'bike_fuel_type': 'PETROL',
            'bike_color': 'Red',
            'bike_condition': 'GOOD',
        }
        response = buyer_client.post('/api/auctions/admin/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestBidding:
    """Tests for bid placement and validation."""

    def test_place_bid_success(self, buyer_client, active_auction):
        bid_amount = float(active_auction.current_price + active_auction.min_increment)
        response = buyer_client.post(
            f'/api/auctions/{active_auction.id}/bids/',
            {'amount': bid_amount},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data['amount']) == bid_amount

    def test_bid_below_minimum(self, buyer_client, active_auction):
        response = buyer_client.post(
            f'/api/auctions/{active_auction.id}/bids/',
            {'amount': float(active_auction.current_price)},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bid_on_own_auction(self, admin_client, active_auction):
        bid_amount = float(active_auction.current_price + active_auction.min_increment)
        response = admin_client.post(
            f'/api/auctions/{active_auction.id}/bids/',
            {'amount': bid_amount},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bid_unauthenticated(self, api_client, active_auction):
        response = api_client.post(
            f'/api/auctions/{active_auction.id}/bids/',
            {'amount': 150000},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_bid_updates_current_price(self, buyer_client, active_auction):
        bid_amount = float(active_auction.current_price + active_auction.min_increment)
        buyer_client.post(
            f'/api/auctions/{active_auction.id}/bids/',
            {'amount': bid_amount},
        )
        active_auction.refresh_from_db()
        assert float(active_auction.current_price) == bid_amount


@pytest.mark.django_db
class TestAuctionLifecycle:
    """Tests for auction status transitions."""

    def test_scheduled_to_active(self, sample_bike, admin_user):
        """Verify model properties for lifecycle states."""
        now = timezone.now()
        auction = Auction.objects.create(
            title='Lifecycle Test',
            bike=sample_bike,
            seller=admin_user,
            start_price=Decimal('100000'),
            current_price=Decimal('100000'),
            min_increment=Decimal('1000'),
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=5),
            status='SCHEDULED',
        )
        assert auction.is_scheduled
        assert not auction.can_accept_bids()

    def test_active_auction_accepts_bids(self, active_auction):
        assert active_auction.is_active
        assert active_auction.can_accept_bids()

    def test_completed_auction_rejects_bids(self, active_auction):
        active_auction.status = 'COMPLETED'
        active_auction.save()
        assert not active_auction.can_accept_bids()

    def test_determine_winner(self, active_auction, buyer_user, buyer2_user):
        Bid.objects.create(amount=Decimal('105000'), auction=active_auction, bidder=buyer_user)
        Bid.objects.create(amount=Decimal('110000'), auction=active_auction, bidder=buyer2_user)

        winner = active_auction.determine_winner()
        assert winner == buyer2_user


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, api_client):
        response = api_client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'

    def test_readiness_endpoint(self, api_client):
        response = api_client.get('/api/health/ready/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['ready'] is True
