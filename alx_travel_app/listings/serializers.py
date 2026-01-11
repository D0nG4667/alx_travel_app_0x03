#!/usr/bin/env python3
"""Serializers for Listing, Booking, and Review models in the travel app."""

from rest_framework import serializers
from django.db.models import Avg
from .models import Listing, Booking, Review, Payment
from drf_spectacular.utils import extend_schema_field


class ReviewSerializer(serializers.ModelSerializer):
    """Serializes Review instances for read-only API exposure.

    Includes reviewer identity, rating, comment, and timestamp.
    Used as a nested serializer within ListingSerializer.
    """

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """Serializes Booking instances for both read and write operations.

    Accepts listing ID for creation, exposes listing and guest names for display.
    Used as a nested serializer within ListingSerializer.
    """

    guest = serializers.StringRelatedField(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), source='listing', write_only=True
    )
    listing = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'listing_id',
            'listing',
            'guest',
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'guest', 'listing', 'created_at']


class ListingSerializer(serializers.ModelSerializer):
    """Serializes Listing instances with nested bookings and reviews.

    Includes host identity, amenities, availability, and computed average rating.
    Designed for detailed API responses and frontend consumption.
    """

    host = serializers.StringRelatedField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    bookings = BookingSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'host',
            'title',
            'description',
            'location',
            'price_per_night',
            'max_guests',
            'amenities',
            'available',
            'average_rating',
            'created_at',
            'updated_at',
            'bookings',
            'reviews',
        ]
        read_only_fields = [
            'id',
            'host',
            'average_rating',
            'created_at',
            'updated_at',
            'bookings',
            'reviews',
        ]

    @extend_schema_field(float)
    def get_average_rating(self, obj) -> float:
        """Compute the average rating from all reviews for this listing."""
        return obj.reviews.aggregate(avg=Avg('rating')).get('avg') or 0.0


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    class Meta:
        model = Payment
        fields = [
            'id',
            'booking_reference',
            'amount',
            'transaction_id',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'transaction_id',
            'status',
            'created_at',
            'updated_at',
        ]
