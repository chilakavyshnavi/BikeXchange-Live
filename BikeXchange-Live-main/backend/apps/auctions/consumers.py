"""
WebSocket consumer for real-time auction bidding.

Handles:
- JWT-based authentication on connection
- Joining/leaving auction rooms
- Real-time bid placement and broadcasting
- Auction status update notifications
"""

import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Auction, Bid

logger = logging.getLogger(__name__)
User = get_user_model()


class AuctionConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for live auction bidding.
    
    Protocol:
        Connect: ws/auctions/<auction_id>/?token=<jwt_access_token>
        
        Client → Server messages:
            {"type": "place_bid", "amount": 55000}
        
        Server → Client messages:
            {"type": "bid_placed", "bid": {...}, "current_price": 55000}
            {"type": "auction_update", "status": "ACTIVE", "time_remaining": 120}
            {"type": "error", "message": "..."}
            {"type": "connection_established", "auction_id": "...", "user": "..."}
    """

    async def connect(self):
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.room_group_name = f'auction_{self.auction_id}'
        self.user = None

        # Authenticate via JWT token in query params
        query_string = self.scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        if token:
            self.user = await self.authenticate_token(token)

        # Join the auction room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # Send connection confirmation
        auction_data = await self.get_auction_data()
        if auction_data:
            await self.send_json({
                'type': 'connection_established',
                'auction_id': str(self.auction_id),
                'user': self.user.username if self.user else None,
                'auction_status': auction_data['status'],
                'current_price': str(auction_data['current_price']),
                'time_remaining': auction_data['time_remaining'],
            })
        else:
            await self.send_json({
                'type': 'error',
                'message': 'Auction not found.',
            })
            await self.close()

        logger.info(
            f'WebSocket connected: auction={self.auction_id}, '
            f'user={self.user.email if self.user else "anonymous"}'
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        logger.debug(
            f'WebSocket disconnected: auction={self.auction_id}, code={close_code}'
        )

    async def receive_json(self, content):
        """Handle incoming messages from the client."""
        msg_type = content.get('type')

        if msg_type == 'place_bid':
            await self.handle_place_bid(content)
        elif msg_type == 'ping':
            await self.send_json({'type': 'pong'})
        else:
            await self.send_json({
                'type': 'error',
                'message': f'Unknown message type: {msg_type}',
            })

    async def handle_place_bid(self, content):
        """Process a bid placement request."""
        if not self.user:
            await self.send_json({
                'type': 'error',
                'message': 'Authentication required to place bids.',
            })
            return

        try:
            amount = Decimal(str(content.get('amount', 0)))
        except (InvalidOperation, TypeError):
            await self.send_json({
                'type': 'error',
                'message': 'Invalid bid amount.',
            })
            return

        # Place bid in database
        result = await self.create_bid(amount)

        if result['success']:
            # Broadcast to all clients in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'bid_placed',
                    'bid': result['bid'],
                    'current_price': str(result['current_price']),
                },
            )
        else:
            await self.send_json({
                'type': 'error',
                'message': result['error'],
            })

    # ─── Group message handlers ───────────────────────────────────────

    async def bid_placed(self, event):
        """Broadcast a new bid to all connected clients."""
        await self.send_json({
            'type': 'bid_placed',
            'bid': event['bid'],
            'current_price': event['current_price'],
        })

    async def auction_update(self, event):
        """Broadcast auction status changes."""
        await self.send_json({
            'type': 'auction_update',
            'status': event['status'],
            'time_remaining': event.get('time_remaining', 0),
            'winner': event.get('winner'),
            'current_price': event.get('current_price'),
        })

    # ─── Database operations ──────────────────────────────────────────

    @database_sync_to_async
    def authenticate_token(self, token):
        """Validate JWT token and return the user."""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist) as e:
            logger.warning(f'WebSocket auth failed: {e}')
            return None

    @database_sync_to_async
    def get_auction_data(self):
        """Fetch current auction state."""
        try:
            auction = Auction.objects.get(pk=self.auction_id)
            return {
                'status': auction.status,
                'current_price': auction.current_price,
                'time_remaining': auction.time_remaining,
            }
        except Auction.DoesNotExist:
            return None

    @database_sync_to_async
    def create_bid(self, amount):
        """Create a bid in the database with validation."""
        try:
            auction = Auction.objects.select_for_update().get(pk=self.auction_id)

            # Validate auction state
            if not auction.can_accept_bids():
                return {'success': False, 'error': 'Auction is not accepting bids.'}

            # Validate seller
            if auction.seller == self.user:
                return {'success': False, 'error': 'Cannot bid on your own auction.'}

            # Validate amount
            min_bid = auction.current_price + auction.min_increment
            if amount < min_bid:
                return {
                    'success': False,
                    'error': f'Minimum bid is ₹{min_bid:,.2f}',
                }

            # Create bid
            bid = Bid.objects.create(
                amount=amount,
                auction=auction,
                bidder=self.user,
            )

            # Update auction price
            auction.current_price = amount
            auction.save(update_fields=['current_price', 'updated_at'])

            logger.info(
                f'Bid placed via WebSocket: ₹{amount:,.2f} on {auction.title} '
                f'by {self.user.email}'
            )

            return {
                'success': True,
                'bid': {
                    'id': str(bid.id),
                    'amount': str(bid.amount),
                    'bidder': {
                        'id': str(self.user.id),
                        'username': self.user.username,
                        'display_name': self.user.display_name,
                    },
                    'created_at': bid.created_at.isoformat(),
                },
                'current_price': amount,
            }

        except Auction.DoesNotExist:
            return {'success': False, 'error': 'Auction not found.'}
        except Exception as e:
            logger.error(f'Bid creation error: {e}', exc_info=True)
            return {'success': False, 'error': 'An error occurred while placing your bid.'}
