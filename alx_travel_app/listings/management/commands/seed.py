#!/usr/bin/env python3
"""Seed the database with realistic listings, bookings, and reviews using Faker."""

from __future__ import annotations

import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from alx_travel_app.listings.models import Listing, Booking, Review
from faker import Faker

User = get_user_model()
fake = Faker()

AMENITIES_POOL = ['WiFi', 'Air Conditioning', 'Kitchen', 'Parking', 'Washer', 'Heating']


class Command(BaseCommand):
    help = 'Seed the database with realistic listings, bookings, and reviews.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=5, help='Number of listings to create'
        )
        parser.add_argument(
            '--reviews', type=int, default=2, help='Reviews per listing'
        )
        parser.add_argument(
            '--bookings', type=int, default=2, help='Bookings per listing'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        review_count = options['reviews']
        booking_count = options['bookings']

        self.stdout.write('🔧 Seeding database with Faker...')

        host = self._get_or_create_user('host_user', 'host@example.com')
        guest = self._get_or_create_user('guest_user', 'guest@example.com')

        for i in range(count):
            listing = Listing.objects.create(
                host=host,
                title=fake.catch_phrase(),
                description=fake.paragraph(nb_sentences=3),
                location=fake.city(),
                price_per_night=Decimal(random.randint(30, 150)),
                max_guests=random.randint(1, 6),
                amenities=random.sample(AMENITIES_POOL, k=random.randint(2, 4)),
                available=True,
            )
            self.stdout.write(f'✅ Created listing: {listing.title}')

            self._create_bookings(listing, guest, booking_count, offset=i)
            self._create_reviews(listing, guest, review_count)

        self.stdout.write(self.style.SUCCESS('🎉 Seeding complete.'))

    def _get_or_create_user(self, username: str, email: str) -> AbstractUser:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': False},
        )
        if created:
            user.set_password('password')
            user.save()
            self.stdout.write(f'👤 Created user: {username}')
        return user

    def _create_bookings(
        self, listing: Listing, guest: AbstractUser, count: int, offset: int
    ):
        for j in range(count):
            start = date.today() + timedelta(days=offset + j * 3)
            end = start + timedelta(days=random.randint(2, 5))
            num_days = (end - start).days
            total_price = listing.price_per_night * Decimal(num_days)
            Booking.objects.create(
                listing=listing,
                guest=guest,
                start_date=start,
                end_date=end,
                total_price=total_price,
                status=Booking.STATUS_CONFIRMED,
            )
            self.stdout.write(f'📅 Booking added for {listing.title} ({start} → {end})')

    def _create_reviews(self, listing: Listing, guest: AbstractUser, count: int):
        for _ in range(count):
            Review.objects.update_or_create(
                listing=listing,
                user=guest,
                defaults={
                    'rating': random.randint(3, 5),
                    'comment': fake.sentence(nb_words=12),
                },
            )
            self.stdout.write(f'⭐ Review added for {listing.title}')
