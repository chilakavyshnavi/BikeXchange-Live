"""
Serializers for bikes, auctions, and bids.

Includes validation logic for bid placement and
nested serialization for detailed auction views.
"""

from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer
from .models import Bike, Auction, Bid


class BikeSerializer(serializers.ModelSerializer):
    """Full bike details serializer."""

    display_name = serializers.ReadOnlyField()

    class Meta:
        model = Bike
        fields = [
            'id', 'make', 'model', 'year', 'mileage', 'engine_cc',
            'fuel_type', 'color', 'condition', 'description', 'images',
            'display_name', 'created_at',
        ]


class BidSerializer(serializers.ModelSerializer):
    """Bid serializer with bidder info."""

    bidder = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'amount', 'bidder', 'created_at']
        read_only_fields = ['id', 'bidder', 'created_at']


class AuctionListSerializer(serializers.ModelSerializer):
    """Compact auction serializer for list views."""

    bike = BikeSerializer(read_only=True)
    seller = UserMinimalSerializer(read_only=True)
    bid_count = serializers.ReadOnlyField()
    time_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Auction
        fields = [
            'id', 'title', 'description', 'bike', 'seller',
            'start_price', 'current_price', 'start_time', 'end_time',
            'status', 'bid_count', 'time_remaining', 'created_at',
        ]


class AuctionDetailSerializer(serializers.ModelSerializer):
    """Full auction detail with bike info, bids, and winner."""

    bike = BikeSerializer(read_only=True)
    seller = UserMinimalSerializer(read_only=True)
    winner = UserMinimalSerializer(read_only=True)
    bids = serializers.SerializerMethodField()
    bid_count = serializers.ReadOnlyField()
    time_remaining = serializers.ReadOnlyField()
    min_next_bid = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            'id', 'title', 'description', 'bike', 'seller',
            'start_price', 'current_price', 'reserve_price',
            'min_increment', 'start_time', 'end_time', 'status',
            'winner', 'bids', 'bid_count', 'time_remaining',
            'min_next_bid', 'created_at', 'updated_at',
        ]

    def get_bids(self, obj):
        """Return the most recent 50 bids."""
        recent_bids = obj.bids.select_related('bidder').order_by('-created_at')[:50]
        return BidSerializer(recent_bids, many=True).data

    def get_min_next_bid(self, obj):
        """Calculate the minimum allowed next bid amount."""
        return float(obj.current_price + obj.min_increment)


class CreateAuctionSerializer(serializers.ModelSerializer):
    """Serializer for creating a new auction with bike details."""

    # Nested bike creation
    bike_make = serializers.CharField(write_only=True)
    bike_model = serializers.CharField(write_only=True)
    bike_year = serializers.IntegerField(write_only=True)
    bike_mileage = serializers.IntegerField(write_only=True)
    bike_engine_cc = serializers.IntegerField(write_only=True)
    bike_fuel_type = serializers.ChoiceField(
        choices=Bike.FuelType.choices,
        write_only=True,
        default='PETROL',
    )
    bike_color = serializers.CharField(write_only=True)
    bike_condition = serializers.ChoiceField(
        choices=Bike.Condition.choices,
        write_only=True,
    )
    bike_description = serializers.CharField(write_only=True, required=False, default='')
    bike_images = serializers.JSONField(write_only=True, required=False, default=list)

    class Meta:
        model = Auction
        fields = [
            'title', 'description', 'start_price', 'reserve_price',
            'min_increment', 'start_time', 'end_time',
            # Bike fields
            'bike_make', 'bike_model', 'bike_year', 'bike_mileage',
            'bike_engine_cc', 'bike_fuel_type', 'bike_color',
            'bike_condition', 'bike_description', 'bike_images',
        ]

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time.',
                })
            if (end_time - start_time).total_seconds() < 300:
                raise serializers.ValidationError({
                    'end_time': 'Auction must last at least 5 minutes.',
                })

        if attrs.get('reserve_price') and attrs.get('start_price'):
            if attrs['reserve_price'] < attrs['start_price']:
                raise serializers.ValidationError({
                    'reserve_price': 'Reserve price cannot be less than start price.',
                })

        return attrs

    def create(self, validated_data):
        # Extract bike fields
        bike_data = {
            'make': validated_data.pop('bike_make'),
            'model': validated_data.pop('bike_model'),
            'year': validated_data.pop('bike_year'),
            'mileage': validated_data.pop('bike_mileage'),
            'engine_cc': validated_data.pop('bike_engine_cc'),
            'fuel_type': validated_data.pop('bike_fuel_type'),
            'color': validated_data.pop('bike_color'),
            'condition': validated_data.pop('bike_condition'),
            'description': validated_data.pop('bike_description', ''),
            'images': validated_data.pop('bike_images', []),
        }

        # Create bike
        bike = Bike.objects.create(**bike_data)

        # Create auction
        auction = Auction.objects.create(
            bike=bike,
            seller=self.context['request'].user,
            current_price=validated_data['start_price'],
            **validated_data,
        )

        return auction


class PlaceBidSerializer(serializers.Serializer):
    """
    Serializer for placing a bid on an auction.
    
    Validates:
    - Auction is currently active
    - Bid amount exceeds current price + minimum increment
    - Bidder is not the auction seller
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        auction = self.context['auction']
        user = self.context['request'].user

        # Check auction is active
        if not auction.can_accept_bids():
            raise serializers.ValidationError('This auction is not currently accepting bids.')

        # Check bidder is not seller
        if auction.seller == user:
            raise serializers.ValidationError('You cannot bid on your own auction.')

        # Check minimum bid amount
        min_bid = auction.current_price + auction.min_increment
        if value < min_bid:
            raise serializers.ValidationError(
                f'Bid must be at least ₹{min_bid:,.2f} '
                f'(current: ₹{auction.current_price:,.2f} + '
                f'increment: ₹{auction.min_increment:,.2f})'
            )

        return value

    def create(self, validated_data):
        auction = self.context['auction']
        user = self.context['request'].user

        bid = Bid.objects.create(
            amount=validated_data['amount'],
            auction=auction,
            bidder=user,
        )

        # Update current price on the auction
        auction.current_price = validated_data['amount']
        auction.save(update_fields=['current_price', 'updated_at'])

        return bid
