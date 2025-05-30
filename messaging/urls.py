from django.urls import path
from .views import InboundMessageAPIView, OutboundMessageAPIView

urlpatterns = [
    path("messages/inbound/", InboundMessageAPIView.as_view(), name="inbound-message"),
    path("messages/outbound/", OutboundMessageAPIView.as_view(), name="outbound-message"),
]