# Hatch Messaging — Take-Home Assignment

This project is a messaging API built with Django 5. It supports sending and receiving messages via SMS, MMS, and Email. Outbound messages are processed asynchronously using Celery with Redis as the message broker.

---

## ✅ Features

- Django 5 + Django REST Framework
- Inbound & outbound messaging endpoints
- Supports SMS, MMS, and Email types
- Redis-backed Celery task queue for async delivery
- Clean, testable codebase with sample test coverage

---

## 🛠️ Requirements

- Python 3.11+
- Redis
- pip (or virtualenv/venv)
- Celery

---

## ⚙️ Setup Instructions

### 1. Clone and set up virtual environment

```bash
git clone <your-fork-url>
cd hatch_messaging
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Redis

Make sure Redis is running locally. You can start it with:

```bash
redis-server
```

If you don’t have Redis installed, install it with:

```bash
brew install redis
```

---

## 🚀 Running the App

### 1. Run migrations

```bash
python manage.py migrate
```

### 2. Start the Celery worker

```bash
celery -A hatch_messaging worker --loglevel=info
```

### 3. Start the Django development server

```bash
python manage.py runserver
```

---

## 📬 API Overview

### Outbound (Queued)

```http
POST /messages/outbound/
```

Example JSON payload:

```json
{
  "from": "user@usehatchapp.com",
  "to": "contact@example.com",
  "type": "email",
  "body": "Hello world!",
  "attachments": [],
  "timestamp": "2024-11-01T14:00:00Z"
}
```

### Inbound (Stored)

```http
POST /messages/inbound/
```

Example JSON payload:

```json
{
  "from": "+18045551234",
  "to": "+12016661234",
  "type": "sms",
  "messaging_provider_id": "abc123",
  "body": "Incoming message",
  "attachments": null,
  "timestamp": "2024-11-01T14:00:00Z"
}
```

---

## 🧪 Running Tests

```bash
python manage.py test
```

Celery `.delay()` calls are mocked in unit tests.

---

## 🧠 Notes

- Tasks are sent to Redis and picked up by Celery workers.
- HTTP requests in Celery tasks use `requests.post(...)` to simulate sending to a provider.
- Redis queue can be inspected with `redis-cli` via `LRANGE celery 0 -1`.
