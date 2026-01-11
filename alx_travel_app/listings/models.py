#!/usr/bin/env python3
"""
Django models for the listings app.

This module defines the core data structures for a travel booking platform,
including:

- Listing: Represents a property available for booking, hosted by a user.
- Booking: Represents a reservation made by a guest for a specific listing.
- Review: Represents a guest's feedback and rating for a listing.

Each model includes appropriate relationships, constraints, and indexing to
ensure data integrity and efficient querying. These models support API
serialization, database seeding, and real-world booking workflows.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Listing(models.Model):
    """A property listing (hosted by a user)."""

    id = models.BigAutoField(primary_key=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    max_guests = models.PositiveIntegerField(default=1)
    amenities = models.JSONField(blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['host']),
            models.Index(fields=['location']),
        ]

    def __str__(self) -> str:
        return f'{self.title} — {self.location}'


class Booking(models.Model):
    """A booking made by a guest for a listing."""

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.BigAutoField(primary_key=True)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='bookings'
    )
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing']),
            models.Index(fields=['guest']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='valid_booking_dates',
            )
        ]

    def __str__(self) -> str:
        return f'Booking {self.id} — {self.listing} ({self.guest})'


class Review(models.Model):
    """A review left by a guest for a listing."""

    id = models.BigAutoField(primary_key=True)
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('listing', 'user')
        indexes = [
            models.Index(fields=['listing']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='valid_rating_range',
            )
        ]

    def __str__(self) -> str:
        return f'Review {self.rating} — {self.listing} by {self.user}'


class Payment(models.Model):
    booking_reference = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Completed', 'Completed'),
            ('Failed', 'Failed'),
        ],
        default='Pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name='valid_payment_amount',
            )
        ]

    def __str__(self):
        return f'{self.booking_reference} - {self.status}'
