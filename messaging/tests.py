from unittest.mock import patch
from uuid import UUID

from django.utils.dateparse import parse_datetime
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from messaging.models import Message
from messaging.utils.message_helpers import build_validated_message_data


class InboundMessageTests(APITestCase):

    @patch("messaging.views.send_message_to_provider.delay")
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
        mock_delay.assert_not_called()

    @patch("messaging.views.send_message_to_provider.delay")
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

    @patch("messaging.views.send_message_to_provider.delay")
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

    def test_inbound_missing_type(self):
        data = {
            "from": "user@usehatchapp.com",
            "to": "contact@gmail.com",
            "body": "Missing type field",
            "timestamp": "2024-11-01T14:00:00Z"
        }
        response = self.client.post("/messages/inbound/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)


class OutboundMessageTests(APITestCase):

    @patch("messaging.views.send_message_to_provider.delay")
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

    @patch("messaging.views.send_message_to_provider.delay")
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


class BuildValidatedMessageDataTests(TestCase):

    def setUp(self):
        self.timestamp = "2024-11-01T14:00:00Z"

    def test_valid_sms(self):
        data = {
            "from": "+1234567890",
            "to": "+1987654321",
            "type": "sms",
            "body": "Test",
            "attachments": [],
            "timestamp": self.timestamp
        }
        enriched, sender, msg_type = build_validated_message_data(data)
        self.assertEqual(msg_type, "sms")
        self.assertEqual(enriched['provider'], "sms_provider")
        self.assertEqual(enriched['type'], "sms")
        self.assertEqual(str(parse_datetime(self.timestamp)), str(enriched['timestamp']))
        self.assertTrue(UUID(enriched['provider_message_id']))

    def test_valid_mms(self):
        data = {
            "from": "+1234567890",
            "to": "+1987654321",
            "type": "mms",
            "body": "Image",
            "attachments": ["url"],
            "timestamp": self.timestamp
        }
        enriched, _, msg_type = build_validated_message_data(data)
        self.assertEqual(msg_type, "mms")
        self.assertEqual(enriched['provider'], "sms_provider")

    def test_valid_email(self):
        data = {
            "from": "a@a.com",
            "to": "b@b.com",
            "type": "email",
            "body": "Hi",
            "timestamp": self.timestamp
        }
        enriched, _, msg_type = build_validated_message_data(data)
        self.assertEqual(msg_type, "email")
        self.assertEqual(enriched['provider'], "email_provider")

    def test_infer_email(self):
        data = {
            "from": "a@a.com",
            "to": "b@b.com",
            "xillio_id": "some-id",
            "body": "Hi",
            "timestamp": self.timestamp
        }
        enriched, _, msg_type = build_validated_message_data(data, require_type=False)
        self.assertEqual(msg_type, "email")
        self.assertEqual(enriched['provider'], "email_provider")

    def test_infer_sms(self):
        data = {
            "from": "+1234567890",
            "to": "+1987654321",
            "messaging_provider_id": "some-id",
            "body": "Hey",
            "timestamp": self.timestamp
        }
        enriched, _, msg_type = build_validated_message_data(data, require_type=False)
        self.assertEqual(msg_type, "sms")
        self.assertEqual(enriched['provider'], "sms_provider")

    def test_invalid_type(self):
        data = {
            "from": "+1234567890",
            "to": "+1987654321",
            "type": "fax",
            "timestamp": self.timestamp
        }
        with self.assertRaisesMessage(ValueError, "Invalid message type: 'fax'"):
            build_validated_message_data(data)

    def test_missing_required_fields(self):
        data = {
            "type": "sms",
            "timestamp": self.timestamp
        }
        with self.assertRaisesMessage(ValueError, "Missing 'from', 'to', or 'type'."):
            build_validated_message_data(data)

    def test_cannot_infer_type(self):
        data = {
            "from": "+1234567890",
            "to": "+1987654321",
            "timestamp": self.timestamp
        }
        with self.assertRaisesMessage(ValueError, "Missing 'type' and unable to infer message type."):
            build_validated_message_data(data, require_type=False)
