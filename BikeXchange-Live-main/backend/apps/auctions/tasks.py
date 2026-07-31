"""
Auction lifecycle scheduler.

Runs a background task that automatically transitions auction states:
    SCHEDULED → ACTIVE  (when start_time is reached)
    ACTIVE → COMPLETED  (when end_time is reached, determines winner)

Uses APScheduler for in-process scheduling.
In production, this would be replaced with Celery Beat + Redis.
"""

import logging

from django.conf import settings
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler

from .models import Auction

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def check_auction_lifecycle():
    """
    Check and transition auction statuses.
    
    This function is called periodically by the scheduler.
    It handles two transitions:
    
    1. SCHEDULED → ACTIVE: When current time >= start_time
    2. ACTIVE → COMPLETED: When current time >= end_time
    """
    now = timezone.now()

    # Transition: SCHEDULED → ACTIVE
    scheduled_auctions = Auction.objects.filter(
        status=Auction.Status.SCHEDULED,
        start_time__lte=now,
    )

    for auction in scheduled_auctions:
        auction.status = Auction.Status.ACTIVE
        auction.save(update_fields=['status', 'updated_at'])
        logger.info(
            f'Auction ACTIVATED: "{auction.title}" (id={auction.id})'
        )

        # Notify connected WebSocket clients
        _notify_auction_update(auction)

    # Transition: ACTIVE → COMPLETED
    expired_auctions = Auction.objects.filter(
        status=Auction.Status.ACTIVE,
        end_time__lte=now,
    )

    for auction in expired_auctions:
        auction.status = Auction.Status.COMPLETED
        auction.save(update_fields=['status', 'updated_at'])

        # Determine winner
        winner = auction.determine_winner()
        winner_info = winner.display_name if winner else 'No winner (no bids or reserve not met)'

        logger.info(
            f'Auction COMPLETED: "{auction.title}" (id={auction.id}) '
            f'final_price=₹{auction.current_price:,.2f} winner={winner_info}'
        )

        # Notify connected WebSocket clients
        _notify_auction_update(auction, winner)


def _notify_auction_update(auction, winner=None):
    """Send auction status update via Channels layer."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'auction_{auction.id}',
                {
                    'type': 'auction_update',
                    'status': auction.status,
                    'time_remaining': auction.time_remaining,
                    'current_price': str(auction.current_price),
                    'winner': {
                        'id': str(winner.id),
                        'username': winner.username,
                        'display_name': winner.display_name,
                    } if winner else None,
                },
            )
    except Exception as e:
        logger.error(f'Failed to send WebSocket notification: {e}')


def start_scheduler():
    """Start the auction lifecycle scheduler."""
    interval = getattr(settings, 'AUCTION_CHECK_INTERVAL_SECONDS', 15)

    if not scheduler.running:
        scheduler.add_job(
            check_auction_lifecycle,
            'interval',
            seconds=interval,
            id='auction_lifecycle_check',
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            f'Auction lifecycle scheduler started '
            f'(checking every {interval}s)'
        )


def stop_scheduler():
    """Stop the auction lifecycle scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info('Auction lifecycle scheduler stopped')
