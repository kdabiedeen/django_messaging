from copy import deepcopy

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError

from .models import Conversation, Message, Participant
from .serializers import MessageSerializer
from .tasks import send_message_to_provider

import uuid


def get_or_create_participant(address):
    if '@' in address:
        return Participant.objects.get_or_create(email=address)
    return Participant.objects.get_or_create(phone=address)


def get_conversation_between(p1, p2):
    return Conversation.objects.get_or_create(
        participant_1=min(p1, p2, key=lambda x: x.id),
        participant_2=max(p1, p2, key=lambda x: x.id)
    )


class InboundMessageAPIView(APIView):
    def post(self, request):
        data = request.data.copy()

        from_address = data.get("from")
        to_address = data.get("to")
        msg_type = data.get("type")

        if not from_address or not to_address or not msg_type:
            return Response({"detail": "Missing 'from', 'to', or 'type'."}, status=400)

        sender, _ = get_or_create_participant(from_address)
        receiver, _ = get_or_create_participant(to_address)

        data['provider_message_id'] = (
                data.get('messaging_provider_id') or
                data.get('xillio_id') or
                str(uuid.uuid4())
        )
        data['provider'] = "sms_provider" if msg_type in ['sms', 'mms'] else "email_provider"
        data['timestamp'] = parse_datetime(data['timestamp'])

        conversation, _ = get_conversation_between(sender, receiver)
        data['conversation'] = conversation.id
        data['sender'] = sender.id
        data['receiver'] = receiver.id

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response({"detail": "Message already exists."}, status=200)
            return Response({"status": "received"}, status=201)

        return Response(serializer.errors, status=400)


class OutboundMessageAPIView(APIView):
    def post(self, request):
        data = request.data.copy()

        from_address = data.get("from")
        to_address = data.get("to")
        msg_type = data.get("type")

        if not from_address or not to_address or not msg_type:
            return Response({"detail": "Missing 'from', 'to', or 'type'."}, status=400)

        sender, _ = get_or_create_participant(from_address)
        receiver, _ = get_or_create_participant(to_address)

        data['provider_message_id'] = str(uuid.uuid4())
        data['provider'] = "sms_provider" if msg_type in ['sms', 'mms'] else "email_provider"
        data['timestamp'] = parse_datetime(data['timestamp'])

        conversation, _ = get_conversation_between(sender, receiver)
        data['conversation'] = conversation.id
        data['sender'] = sender.id
        data['receiver'] = receiver.id

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            provider_url = (
                "https://www.provider.app/api/messages" if msg_type in ['sms', 'mms']
                else "https://www.mailplus.app/api/email"
            )

            safe_data = deepcopy(data)
            safe_data['timestamp'] = safe_data['timestamp'].isoformat()

            send_message_to_provider.delay(safe_data, provider_url)
            return Response({"status": "queued"}, status=202)

        return Response(serializer.errors, status=400)
