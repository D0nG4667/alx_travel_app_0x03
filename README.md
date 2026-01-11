# ALX Travel App

A modular, scalable Django-based travel listing platform with REST APIs, Swagger documentation, MySQL database integration, and Docker support. This project is built following industry-standard practices for maintainable backend development and scalable web applications.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Data Seeding](#data-seeding)
- [Docker Setup](#docker-setup)
- [Future Enhancements](#future-enhancements)

---

## Project Overview

`alx_travel_app` is a travel listing platform designed with a modular Django backend. It leverages:

- **Django REST Framework (DRF)** for building RESTful APIs.
- **drf-spectacular** for OpenAPI schema generation and Swagger documentation.
- **MySQL** as the primary relational database.
- **Celery and RabbitMQ** for task queuing and background processing.
- **Docker** for containerized deployment.

This setup ensures scalability, maintainability, and readiness for production.

---

## Features

- RESTful APIs for listings, bookings, and reviews.
- Nested serializers with computed fields (e.g., average rating).
- Management command for realistic database seeding.
- Environment-driven configuration using `.env` and `django-environ`.
- Swagger UI (`/docs/`) and ReDoc (`/redoc/`) documentation.
- Containerized services for MySQL and RabbitMQ using Docker Compose.

---

## Requirements

- Python 3.12+
- Django 5.x
- MySQL 8.x
- Docker & Docker Compose (optional for local container setup)
- RabbitMQ (required for Celery background tasks)

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/DonG4667/alx_travel_app_0x02.git
   cd alx_travel_app_0x02
   ```

2. **Create a virtual environment:**

   ```bash
   uv venv
   source venv/bin/activate  # Linux / Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**

   ```bash
   uv sync  # Recommended
   ```

   Or:

   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Configuration

1. Copy the `.env.example` file to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Update your `.env` file with:

   ```env
   DATABASE_URL=mysql://user:password@localhost:3306/alx_travel_app
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
   ```

---

## Database Setup

1. Create the MySQL database (if not using Docker):

   ```sql
   CREATE DATABASE alx_travel_app;
   ```

2. Apply migrations:

   ```bash
   python manage.py migrate
   ```

3. (Optional) Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

---

## Running the Project

1. **Start Django server:**

   ```bash
   python manage.py runserver
   ```

2. Access the app at:

   ```web
   http://127.0.0.1:8000/
   ```

---

## API Documentation

Swagger and ReDoc endpoints:

- Swagger UI: [http://127.0.0.1:8000/docs/](http://127.0.0.1:8000/docs/)
- ReDoc: [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

These endpoints automatically document all API routes using `drf-spectacular`.

---

## Data Seeding

To populate the database with sample listings, bookings, and reviews:

```bash
python manage.py seed --count 3 --bookings 2 --reviews 2
```

- `--count`: Number of listings to create
- `--bookings`: Bookings per listing
- `--reviews`: Reviews per listing

This command creates realistic data for development and testing, including randomized amenities and review content.

---

## Docker Setup

1. **Start services with Docker Compose:**

   ```bash
   docker-compose up -d
   ```

2. Services included:

   - **Django app**
   - **MySQL**
   - **RabbitMQ**

3. Apply migrations inside the Django container:

   ```bash
   docker-compose exec django python manage.py migrate
   ```

4. Access the Django app at `http://localhost:8000/`.

---

## Future Enhancements

- Implement user authentication and role-based permissions.
- Add advanced search and filtering for listings.
- Integrate frontend SPA (React or Next.js) with REST API.
- Add background tasks for notifications, emails, and reporting.
- Enable image uploads and media storage for listings.
- Implement caching strategies for performance optimization.

## Payment Integration with Chapa

### Setup

- Add `.env` with `CHAPA_SECRET_KEY`.
- Run migrations for `Payment` model.

### Endpoints

- `POST /payments/initiate/` → Initiates payment, returns checkout URL.
- `GET /payments/verify/?tx_ref=...` → Verifies payment status.

### Workflow

1. User books a listing.
2. Payment initiated via Chapa.
3. User completes payment.
4. Verification updates status in DB.
5. Confirmation email sent via Celery.

### Testing

- Use Chapa sandbox environment.
- Verify logs and DB updates.
- Screenshots included in `/docs/screenshots`.

Gabriel, let’s turn this into a clean, production‑ready Celery + RabbitMQ background‑task setup for **alx_travel_app_0x03**. I’ll give you a complete, correct implementation across:

- **alx_travel_app/settings.py**
- **alx_travel_app/celery.py**
- **listings/tasks.py**
- **listings/views.py**
- **README.md updates**

Everything below is structured so you can drop it directly into your project and have Celery running asynchronously with RabbitMQ.

---

## 🚀 Celery + RabbitMQ + Email Notifications (Full Implementation)

## 1. Project Structure (expected)

```folder
alx_travel_app_0x03/
│
├── alx_travel_app/
│   ├── __init__.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│
├── listings/
│   ├── tasks.py
│   ├── views.py
│   ├── models.py
│   ├── serializers.py
│
└── README.md
```

---

## 2. **settings.py** — Celery + Email Configuration

Add this inside `alx_travel_app/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = "amqp://guest:guest@rabbitmq:5672//"
CELERY_RESULT_BACKEND = "rpc://"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Email Backend (for development)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your_email@gmail.com"
EMAIL_HOST_PASSWORD = "your_app_password"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

---

## 3. **celery.py** — Celery App Initialization

Create `alx_travel_app/celery.py`:

```python
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

app = Celery("alx_travel_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

Modify `alx_travel_app/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

---

## 4. **listings/tasks.py** — Email Task

```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(user_email, listing_title):
    subject = "Booking Confirmation"
    message = f"Your booking for {listing_title} has been confirmed!"
    send_mail(subject, message, None, [user_email])
    return "Email sent successfully"
```

---

## 5. **listings/views.py** — Trigger Task on Booking Creation

Inside your `BookingViewSet`:

```python
from rest_framework import viewsets
from .models import Booking
from .serializers import BookingSerializer
from .tasks import send_booking_confirmation_email

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        user_email = booking.user.email
        listing_title = booking.listing.title

        # Trigger Celery task
        send_booking_confirmation_email.delay(user_email, listing_title)
```

---

## 🟢 6. Background Tasks with Celery + RabbitMQ

This project uses **Celery** and **RabbitMQ** to send booking confirmation emails asynchronously.

### Start RabbitMQ

```bash
docker compose up -d rabbitmq
```

### Start Celery Worker

```bash
celery -A alx_travel_app worker -l info
```

### Triggering Email

When a booking is created via API:

```sh
POST /api/bookings/
```

Celery automatically sends a confirmation email in the background.

---

## **7. Testing the Background Task**

### 1. Start RabbitMQ

```bash
docker compose up -d rabbitmq
```

### 2. Start Celery Worker

```bash
celery -A alx_travel_app worker -l info
```

### 3. Create a booking

Use Postman or Django admin.

### 4. Check console output

If using console backend, you’ll see:

```sh
Your booking for <listing> has been confirmed!
```
