"""
Management command to seed the database with sample data.

Creates demo users, bikes, and auctions for development and testing.
Usage: python manage.py seed_data
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.auctions.models import Bike, Auction, Bid

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample bikes, auctions, and users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Bid.objects.all().delete()
            Auction.objects.all().delete()
            Bike.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('[*] Seeding Vutto Bike Auction Platform...\n')

        # Create users
        admin = self._create_users()

        # Create bikes and auctions
        self._create_auctions(admin)

        self.stdout.write(self.style.SUCCESS('\n[OK] Seeding complete!'))
        self.stdout.write(self.style.SUCCESS('   Admin: admin@vutto.com / admin123'))
        self.stdout.write(self.style.SUCCESS('   Buyers: buyer1@test.com / buyer123, etc.'))

    def _create_users(self):
        """Create admin and demo buyer accounts."""
        self.stdout.write('  Creating users...')

        # Admin user
        admin, created = User.objects.get_or_create(
            email='admin@vutto.com',
            defaults={
                'username': 'admin',
                'first_name': 'Vutto',
                'last_name': 'Admin',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'    [+] Admin: {admin.email}')

        # Buyer users
        buyers = [
            {'email': 'buyer1@test.com', 'username': 'rahul_m', 'first_name': 'Rahul', 'last_name': 'Mehta', 'phone': '+91-9876543210'},
            {'email': 'buyer2@test.com', 'username': 'priya_s', 'first_name': 'Priya', 'last_name': 'Sharma', 'phone': '+91-9876543211'},
            {'email': 'buyer3@test.com', 'username': 'arjun_k', 'first_name': 'Arjun', 'last_name': 'Kumar', 'phone': '+91-9876543212'},
        ]

        for buyer_data in buyers:
            user, created = User.objects.get_or_create(
                email=buyer_data['email'],
                defaults={**buyer_data, 'role': 'BUYER'},
            )
            if created:
                user.set_password('buyer123')
                user.save()
                self.stdout.write(f'    [+] Buyer: {user.email}')

        return admin

    def _create_auctions(self, admin):
        """Create sample bikes and auctions in various states."""
        self.stdout.write('  Creating bikes and auctions...')

        now = timezone.now()

        bikes_data = [
            {
                'make': 'Royal Enfield', 'model': 'Classic 350', 'year': 2022,
                'mileage': 12000, 'engine_cc': 349, 'fuel_type': 'PETROL',
                'color': 'Stealth Black', 'condition': 'EXCELLENT',
                'description': 'Well-maintained Classic 350 with recent service. Single owner, garage kept. Includes crash guard and touring accessories.',
                'images': ['/bikes/classic350.jpg'],
            },
            {
                'make': 'KTM', 'model': 'Duke 390', 'year': 2023,
                'mileage': 5000, 'engine_cc': 373, 'fuel_type': 'PETROL',
                'color': 'Orange', 'condition': 'EXCELLENT',
                'description': 'Nearly new Duke 390 with only 5000 km. Performance exhaust installed. Full service history available.',
                'images': ['/bikes/duke390.jpg'],
            },
            {
                'make': 'Bajaj', 'model': 'Pulsar NS200', 'year': 2021,
                'mileage': 25000, 'engine_cc': 199, 'fuel_type': 'PETROL',
                'color': 'Red', 'condition': 'GOOD',
                'description': 'Reliable Pulsar NS200 with ABS. Regular maintenance done at authorized service center.',
                'images': ['/bikes/ns200.jpg'],
            },
            {
                'make': 'Honda', 'model': 'CB300R', 'year': 2023,
                'mileage': 3000, 'engine_cc': 286, 'fuel_type': 'PETROL',
                'color': 'Matte Silver', 'condition': 'EXCELLENT',
                'description': 'Premium neo-retro cafe racer. Barely used, still under warranty. A true head-turner.',
                'images': ['/bikes/cb300r.jpg'],
            },
            {
                'make': 'Yamaha', 'model': 'MT-15 V2', 'year': 2022,
                'mileage': 15000, 'engine_cc': 155, 'fuel_type': 'PETROL',
                'color': 'Dark Matt Blue', 'condition': 'GOOD',
                'description': 'Streetfighter styling with VVA engine. Great city commuter with sporty performance.',
                'images': ['/bikes/mt15.jpg'],
            },
            {
                'make': 'Royal Enfield', 'model': 'Himalayan 450', 'year': 2024,
                'mileage': 1500, 'engine_cc': 452, 'fuel_type': 'PETROL',
                'color': 'Slate Himalayan Salt', 'condition': 'EXCELLENT',
                'description': 'Brand new Himalayan 450! Adventure-ready with Sherpa 450 engine. Pannier racks included.',
                'images': ['/bikes/himalayan450.jpg'],
            },
            {
                'make': 'Kawasaki', 'model': 'Ninja 300', 'year': 2021,
                'mileage': 18000, 'engine_cc': 296, 'fuel_type': 'PETROL',
                'color': 'Lime Green', 'condition': 'GOOD',
                'description': 'Iconic Ninja 300 in signature Kawasaki green. Smooth parallel-twin engine. Track day ready.',
                'images': ['/bikes/ninja300.jpg'],
            },
            {
                'make': 'TVS', 'model': 'Apache RR 310', 'year': 2023,
                'mileage': 8000, 'engine_cc': 312, 'fuel_type': 'PETROL',
                'color': 'Racing Red', 'condition': 'EXCELLENT',
                'description': 'Full-faired sportbike with ride modes and SmartXonnect. BMW-derived engine for reliability.',
                'images': ['/bikes/rr310.jpg'],
            },
            {
                'make': 'Suzuki', 'model': 'Gixxer SF 250', 'year': 2022,
                'mileage': 10000, 'engine_cc': 249, 'fuel_type': 'PETROL',
                'color': 'Metallic Triton Blue', 'condition': 'GOOD',
                'description': 'Oil-cooled sportbike with clip-on handlebars. Great value for money with Suzuki reliability.',
                'images': ['/bikes/gixxer250.jpg'],
            },
            {
                'make': 'Husqvarna', 'model': 'Svartpilen 250', 'year': 2022,
                'mileage': 7000, 'engine_cc': 248, 'fuel_type': 'PETROL',
                'color': 'Black', 'condition': 'EXCELLENT',
                'description': 'Swedish-designed scrambler with cafe racer vibes. KTM-derived engine. Unique and stylish.',
                'images': ['/bikes/svartpilen250.jpg'],
            },
        ]

        auctions_config = [
            # Active auctions (currently running)
            {'bike_idx': 0, 'title': '2022 Royal Enfield Classic 350 - Stealth Black Edition',
             'start_price': 125000, 'current_price': 142000, 'min_increment': 1000,
             'start_time': now - timedelta(hours=2), 'end_time': now + timedelta(hours=4),
             'status': 'ACTIVE', 'num_bids': 5},

            {'bike_idx': 1, 'title': '2023 KTM Duke 390 - Low Mileage Beast',
             'start_price': 200000, 'current_price': 225000, 'min_increment': 2000,
             'start_time': now - timedelta(hours=1), 'end_time': now + timedelta(hours=6),
             'status': 'ACTIVE', 'num_bids': 3},

            {'bike_idx': 2, 'title': 'Bajaj Pulsar NS200 ABS - Reliable Daily Rider',
             'start_price': 75000, 'current_price': 82000, 'min_increment': 500,
             'start_time': now - timedelta(hours=3), 'end_time': now + timedelta(hours=2),
             'status': 'ACTIVE', 'num_bids': 4},

            {'bike_idx': 3, 'title': 'Honda CB300R - Premium Cafe Racer Under Warranty',
             'start_price': 190000, 'current_price': 190000, 'min_increment': 2000,
             'start_time': now - timedelta(minutes=30), 'end_time': now + timedelta(hours=8),
             'status': 'ACTIVE', 'num_bids': 0},

            # Scheduled auctions (upcoming)
            {'bike_idx': 4, 'title': 'Yamaha MT-15 V2 - Street Fighter Style',
             'start_price': 110000, 'current_price': 110000, 'min_increment': 1000,
             'start_time': now + timedelta(hours=12), 'end_time': now + timedelta(hours=24),
             'status': 'SCHEDULED', 'num_bids': 0},

            {'bike_idx': 5, 'title': '2024 Royal Enfield Himalayan 450 - Almost New!',
             'start_price': 250000, 'current_price': 250000, 'min_increment': 3000,
             'start_time': now + timedelta(hours=6), 'end_time': now + timedelta(hours=18),
             'status': 'SCHEDULED', 'num_bids': 0},

            {'bike_idx': 6, 'title': 'Kawasaki Ninja 300 - Track-Ready Green Machine',
             'start_price': 180000, 'current_price': 180000, 'min_increment': 2000,
             'start_time': now + timedelta(days=1), 'end_time': now + timedelta(days=1, hours=12),
             'status': 'SCHEDULED', 'num_bids': 0},

            # Completed auctions
            {'bike_idx': 7, 'title': 'TVS Apache RR 310 - Full Faired Sportbike',
             'start_price': 175000, 'current_price': 198500, 'min_increment': 1500,
             'start_time': now - timedelta(days=2), 'end_time': now - timedelta(days=1),
             'status': 'COMPLETED', 'num_bids': 8},

            {'bike_idx': 8, 'title': 'Suzuki Gixxer SF 250 - Sport Touring Ready',
             'start_price': 140000, 'current_price': 156000, 'min_increment': 1000,
             'start_time': now - timedelta(days=3), 'end_time': now - timedelta(days=2),
             'status': 'COMPLETED', 'num_bids': 6},

            # Cancelled auction
            {'bike_idx': 9, 'title': 'Husqvarna Svartpilen 250 - Swedish Design',
             'start_price': 160000, 'current_price': 160000, 'min_increment': 1500,
             'start_time': now - timedelta(days=1), 'end_time': now + timedelta(hours=6),
             'status': 'CANCELLED', 'num_bids': 0},
        ]

        buyers = list(User.objects.filter(role='BUYER'))

        for config in auctions_config:
            bike_data = bikes_data[config['bike_idx']]
            bike, _ = Bike.objects.get_or_create(
                make=bike_data['make'],
                model=bike_data['model'],
                year=bike_data['year'],
                defaults=bike_data,
            )

            # Skip if auction already exists for this bike
            if Auction.objects.filter(bike=bike).exists():
                continue

            auction = Auction.objects.create(
                title=config['title'],
                description=bike_data['description'],
                bike=bike,
                seller=admin,
                start_price=Decimal(str(config['start_price'])),
                current_price=Decimal(str(config['current_price'])),
                min_increment=Decimal(str(config['min_increment'])),
                start_time=config['start_time'],
                end_time=config['end_time'],
                status=config['status'],
            )

            # Create some sample bids for active and completed auctions
            if config['num_bids'] > 0 and buyers:
                current = Decimal(str(config['start_price']))
                increment = Decimal(str(config['min_increment']))

                for i in range(config['num_bids']):
                    current += increment
                    bidder = buyers[i % len(buyers)]
                    bid_time = config['start_time'] + timedelta(minutes=(i + 1) * 10)

                    Bid.objects.create(
                        amount=current,
                        auction=auction,
                        bidder=bidder,
                        created_at=bid_time,
                    )

                # Update current price
                auction.current_price = current
                auction.save(update_fields=['current_price'])

                # Set winner for completed auctions
                if config['status'] == 'COMPLETED':
                    highest_bid = auction.bids.order_by('-amount').first()
                    if highest_bid:
                        auction.winner = highest_bid.bidder
                        auction.save(update_fields=['winner'])

            self.stdout.write(f'    [+] {auction.title} [{auction.status}]')
