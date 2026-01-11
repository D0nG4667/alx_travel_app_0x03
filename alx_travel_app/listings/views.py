#!/usr/bin/env python3
"""ViewSets for Listing, Booking, Review, and Payment endpoints with schema annotations."""

import requests
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Listing, Booking, Review, Payment
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer

# -----------------------------
# Custom permission for Listings
# -----------------------------
class IsHostOrReadOnly(permissions.BasePermission):
    """Custom permission to allow only the host to edit or delete their listings."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'host', None) == request.user


# -----------------------------
# Listing ViewSet
# -----------------------------
@extend_schema_view(
    list=extend_schema(
        summary='List all listings',
        description='Retrieve a list of all available property listings, including nested bookings and reviews.',
    ),
    retrieve=extend_schema(
        summary='Retrieve a specific listing',
        description='Get detailed information about a single listing, including its bookings and reviews.',
    ),
    create=extend_schema(
        summary='Create a new listing',
        description='Authenticated users can create a new property listing. Host is set automatically.',
    ),
    update=extend_schema(
        summary='Update a listing',
        description='Modify an existing listing. Only the host can update their own listings.',
    ),
    destroy=extend_schema(
        summary='Delete a listing',
        description='Remove a listing from the platform. Only the host can delete their own listings.',
    ),
)
class ListingViewSet(viewsets.ModelViewSet):
    """Handles CRUD operations for property listings."""

    queryset = Listing.objects.select_related('host').all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsHostOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


# -----------------------------
# Booking ViewSet
# -----------------------------
@extend_schema_view(
    list=extend_schema(
        summary='List all bookings',
        description='Retrieve all bookings made by users. Admins may see all; users see their own.',
    ),
    retrieve=extend_schema(
        summary='Retrieve a specific booking',
        description='Get details of a specific booking, including listing and guest info.',
    ),
    create=extend_schema(
        summary='Create a new booking',
        description='Authenticated users can book a listing by providing dates and listing ID.',
    ),
)
class BookingViewSet(viewsets.ModelViewSet):
    """Handles bookings for listings."""

    queryset = Booking.objects.select_related('guest', 'listing__host').all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary='List all reviews',
        description='Retrieve all reviews left by users across listings.',
    ),
    retrieve=extend_schema(
        summary='Retrieve a specific review',
        description='Get details of a specific review, including rating and comment.',
    ),
    create=extend_schema(
        summary='Submit a review',
        description='Authenticated users can leave one review per listing. Ratings must be 1–5.',
    ),
)
class ReviewViewSet(viewsets.ModelViewSet):
    """Handles reviews for listings."""

    queryset = Review.objects.select_related('user', 'listing').all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -----------------------------
# Payment ViewSet
# -----------------------------
class PaymentViewSet(viewsets.ModelViewSet):
    """Handles payment operations with Chapa integration."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Initiate a payment",
        description="Start a payment transaction with Chapa. Returns a checkout URL.",
        responses={200: {"type": "object", "properties": {"checkout_url": {"type": "string"}}}},
    )
    @action(detail=False, methods=["post"], url_path="initiate")
    def initiate(self, request):
        booking_ref = request.data.get("booking_reference")
        amount = request.data.get("amount")

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        data = {
            "amount": amount,
            "currency": "ETB",
            "tx_ref": booking_ref,
            "return_url": "http://localhost:8000/api/payments/verify/"
        }

        response = requests.post(
            f"{settings.CHAPA_BASE_URL}/transaction/initialize",
            headers=headers,
            data=data
        )
        resp_json = response.json()

        if resp_json.get("status") == "success":
            transaction_id = resp_json["data"]["tx_ref"]
            Payment.objects.create(
                booking_reference=booking_ref,
                amount=amount,
                transaction_id=transaction_id,
                status="Pending"
            )
            return Response({"checkout_url": resp_json["data"]["checkout_url"]})
        return Response({"error": "Payment initiation failed"}, status=400)

    @extend_schema(
        summary="Verify a payment",
        description="Verify the status of a payment transaction with Chapa.",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
    )
    @action(detail=False, methods=["get"], url_path="verify")
    def verify(self, request):
        tx_ref = request.query_params.get("tx_ref")
        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.get(
            f"{settings.CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=headers
        )
        resp_json = response.json()

        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
            if resp_json.get("status") == "success":
                payment.status = "Completed"
                payment.save()
                return Response({"status": "Payment successful"})
            else:
                payment.status = "Failed"
                payment.save()
                return Response({"status": "Payment failed"})
        except Payment.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)