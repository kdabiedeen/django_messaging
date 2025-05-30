from copy import deepcopy

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError

from .constants import PROVIDER_URLS
from .serializers import MessageSerializer
from .tasks import send_message_to_provider
from .utils.message_helpers import build_validated_message_data


class InboundMessageAPIView(APIView):
    def post(self, request):
        try:
            data, sender, _ = build_validated_message_data(request.data, require_type=False)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

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
        try:
            data, sender, msg_type = build_validated_message_data(request.data, require_type=True)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            safe_data = deepcopy(data)
            safe_data['timestamp'] = safe_data['timestamp'].isoformat()

            send_message_to_provider.delay(
                safe_data,
                PROVIDER_URLS.get(msg_type)
            )

            return Response({"status": "queued"}, status=202)

        return Response(serializer.errors, status=400)
