"""
Django signals for auction-related events.

Handles post-save logging and notifications.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Auction, Bid

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Auction)
def log_auction_status_change(sender, instance, created, **kwargs):
    """Log auction creation and status changes."""
    if created:
        logger.info(
            f'Auction created: "{instance.title}" (id={instance.id}) '
            f'status={instance.status} start={instance.start_time} end={instance.end_time}'
        )
    else:
        update_fields = kwargs.get('update_fields')
        if update_fields and 'status' in update_fields:
            logger.info(
                f'Auction status changed: "{instance.title}" (id={instance.id}) '
                f'→ {instance.status}'
            )


@receiver(post_save, sender=Bid)
def log_bid_placed(sender, instance, created, **kwargs):
    """Log new bid placements."""
    if created:
        logger.info(
            f'Bid recorded: Rs.{instance.amount:,.2f} on "{instance.auction.title}" '
            f'by {instance.bidder.email}'
        )
