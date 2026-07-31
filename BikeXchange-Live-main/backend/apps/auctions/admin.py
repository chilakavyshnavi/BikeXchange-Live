"""
Django admin configuration for Auction models.
"""

from django.contrib import admin
from .models import Bike, Auction, Bid


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'year', 'engine_cc', 'condition', 'color', 'created_at']
    list_filter = ['make', 'condition', 'fuel_type', 'year']
    search_fields = ['make', 'model']
    ordering = ['-created_at']


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'get_bike', 'status', 'start_price',
        'current_price', 'start_time', 'end_time', 'get_bid_count',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'bike__make', 'bike__model']
    ordering = ['-created_at']
    readonly_fields = ['current_price', 'winner', 'created_at', 'updated_at']

    def get_bike(self, obj):
        return obj.bike.display_name
    get_bike.short_description = 'Bike'

    def get_bid_count(self, obj):
        return obj.bids.count()
    get_bid_count.short_description = 'Bids'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['get_auction', 'get_bidder', 'amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['auction__title', 'bidder__email']
    ordering = ['-created_at']
    readonly_fields = ['auction', 'bidder', 'amount', 'created_at']

    def get_auction(self, obj):
        return obj.auction.title
    get_auction.short_description = 'Auction'

    def get_bidder(self, obj):
        return obj.bidder.email
    get_bidder.short_description = 'Bidder'
