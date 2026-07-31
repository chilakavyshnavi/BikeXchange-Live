"""
Models for the auction system: Bike, Auction, and Bid.

Implements the core domain with proper indexing, constraints,
and lifecycle management methods.
"""

import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Bike(models.Model):
    """
    Represents a motorcycle listed for auction.
    
    Stores vehicle specifications, condition assessment,
    and image references.
    """

    class FuelType(models.TextChoices):
        PETROL = 'PETROL', 'Petrol'
        DIESEL = 'DIESEL', 'Diesel'
        ELECTRIC = 'ELECTRIC', 'Electric'

    class Condition(models.TextChoices):
        EXCELLENT = 'EXCELLENT', 'Excellent'
        GOOD = 'GOOD', 'Good'
        FAIR = 'FAIR', 'Fair'
        POOR = 'POOR', 'Poor'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    make = models.CharField(max_length=100, db_index=True)  # e.g., "Royal Enfield"
    model = models.CharField(max_length=100)  # e.g., "Classic 350"
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    mileage = models.PositiveIntegerField(help_text='Mileage in kilometers')
    engine_cc = models.PositiveIntegerField(help_text='Engine displacement in CC')
    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        default=FuelType.PETROL,
    )
    color = models.CharField(max_length=50)
    condition = models.CharField(
        max_length=10,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    description = models.TextField(blank=True, default='')
    images = models.JSONField(
        default=list,
        help_text='List of image URLs/paths',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bike'
        verbose_name_plural = 'Bikes'

    def __str__(self):
        return f'{self.year} {self.make} {self.model}'

    @property
    def display_name(self):
        return f'{self.year} {self.make} {self.model}'


class Auction(models.Model):
    """
    Represents a live auction for a motorcycle.
    
    Manages the auction lifecycle: SCHEDULED → ACTIVE → COMPLETED/CANCELLED.
    Supports real-time bidding with minimum increment enforcement.
    """

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    bike = models.OneToOneField(
        Bike,
        on_delete=models.CASCADE,
        related_name='auction',
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auctions_created',
    )
    start_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reserve_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum price for the auction to be valid (optional)',
    )
    min_increment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500,
        help_text='Minimum bid increment in INR',
    )
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_auctions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Auction'
        verbose_name_plural = 'Auctions'
        indexes = [
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['status', 'end_time']),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_scheduled(self):
        return self.status == self.Status.SCHEDULED

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def time_remaining(self):
        """Returns remaining seconds or 0 if ended."""
        if self.status != self.Status.ACTIVE:
            return 0
        remaining = (self.end_time - timezone.now()).total_seconds()
        return max(0, int(remaining))

    @property
    def bid_count(self):
        return self.bids.count()

    def can_accept_bids(self):
        """Check if the auction can currently accept new bids."""
        return (
            self.status == self.Status.ACTIVE
            and timezone.now() < self.end_time
        )

    def get_highest_bid(self):
        """Return the highest bid for this auction."""
        return self.bids.order_by('-amount').first()

    def determine_winner(self):
        """Set the winner as the highest bidder."""
        highest = self.get_highest_bid()
        if highest:
            # Check reserve price
            if self.reserve_price and highest.amount < self.reserve_price:
                return None
            self.winner = highest.bidder
            self.save(update_fields=['winner'])
            return highest.bidder
        return None


class Bid(models.Model):
    """
    Represents a bid placed by a user on an auction.
    
    Bids are immutable once created. The highest bid
    determines the auction winner.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bid'
        verbose_name_plural = 'Bids'
        indexes = [
            models.Index(fields=['auction', '-amount']),
            models.Index(fields=['bidder', '-created_at']),
        ]

    def __str__(self):
        return f'₹{self.amount:,.2f} by {self.bidder.display_name} on {self.auction.title}'
