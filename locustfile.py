from locust import HttpUser, task, between
import uuid
import random
from datetime import datetime

class MessagingUser(HttpUser):
    wait_time = between(0.5, 2)  # Simulates user think-time between requests

    @task(1)
    def send_sms(self):
        payload = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": str(uuid.uuid4()),
            "body": "Stress test message",
            "attachments": None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.post("/api/messages/", json=payload)

    @task(1)
    def send_mms(self):
        payload = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "mms",
            "messaging_provider_id": str(uuid.uuid4()),
            "body": "Stress test MMS",
            "attachments": ["https://example.com/image.jpg"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.post("/api/messages/", json=payload)

    @task(1)
    def send_email(self):
        payload = {
            "from": "user@usehatchapp.com",
            "to": "contact@gmail.com",
            "xillio_id": str(uuid.uuid4()),
            "body": "<html><body>Stress test email</body></html>",
            "attachments": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.post("/api/messages/", json=payload)
