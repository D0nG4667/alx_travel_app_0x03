from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(user_email, listing_title):
    subject = "Booking Confirmation"
    message = f"Your booking for {listing_title} has been confirmed!"
    send_mail(subject, message, None, [user_email])
    return "Email sent successfully"
