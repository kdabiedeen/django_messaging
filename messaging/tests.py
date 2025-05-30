from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from messaging.models import Message


@patch("messaging.views.send_message_to_provider.delay")
class MessageTests(APITestCase):

    def test_outbound_sms(self, mock_delay):
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Hello via SMS",
            "attachments": [],
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/outbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Message.objects.count(), 1)
        mock_delay.assert_called_once()

    def test_outbound_email(self, mock_delay):
        data = {
            "from": "user@usehatchapp.com",
            "to": "contact@gmail.com",
            "type": "email",
            "body": "HTML email <b>here</b>",
            "attachments": ["attachment-url"],
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/outbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Message.objects.count(), 1)
        mock_delay.assert_called_once()

    def test_inbound_sms(self, mock_delay):
        data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "message-1",
            "body": "Hello inbound SMS",
            "attachments": None,
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/inbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        mock_delay.assert_not_called()  # Only outbound uses .delay()

    def test_inbound_mms(self, mock_delay):
        data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "mms",
            "messaging_provider_id": "message-2",
            "body": "MMS test",
            "attachments": ["attachment-url"],
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/inbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        mock_delay.assert_not_called()

    def test_inbound_email(self, mock_delay):
        data = {
            "from": "user@usehatchapp.com",
            "to": "contact@gmail.com",
            "type": "email",
            "xillio_id": "message-3",
            "body": "<html><body>Email content</body></html>",
            "attachments": ["attachment-url"],
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/inbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        mock_delay.assert_not_called()
