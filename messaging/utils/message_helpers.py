import uuid
from django.utils.dateparse import parse_datetime
from messaging.models import Participant, Conversation


def get_or_create_participant(address):
    if '@' in address:
        return Participant.objects.get_or_create(email=address)
    return Participant.objects.get_or_create(phone=address)


def get_conversation_between(p1, p2):
    return Conversation.objects.get_or_create(
        participant_1=min(p1, p2, key=lambda x: x.id),
        participant_2=max(p1, p2, key=lambda x: x.id)
    )


def build_validated_message_data(data, require_type=True):
    from_address = data.get("from")
    to_address = data.get("to")

    if require_type:
        msg_type = data.get("type")
    elif "xillio_id" in data:
        msg_type = "email"
    else:
        msg_type = "sms"

    if not from_address or not to_address or (require_type and not msg_type):
        raise ValueError("Missing 'from', 'to', or 'type'.")

    sender, _ = get_or_create_participant(from_address)
    receiver, _ = get_or_create_participant(to_address)

    enriched_data = data.copy()
    enriched_data['provider_message_id'] = (
            data.get('messaging_provider_id') or
            data.get('xillio_id') or
            str(uuid.uuid4())
    )
    enriched_data['provider'] = (
        "sms_provider" if msg_type in ['sms', 'mms'] else "email_provider"
    )
    enriched_data['timestamp'] = parse_datetime(data['timestamp'])

    conversation, _ = get_conversation_between(sender, receiver)
    enriched_data['conversation'] = conversation.id
    enriched_data['sender'] = sender.id
    enriched_data['receiver'] = receiver.id
    enriched_data['type'] = msg_type

    return enriched_data, sender, msg_type
