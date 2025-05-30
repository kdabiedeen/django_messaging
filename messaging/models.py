from django.db import models


class Participant(models.Model):
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email or self.phone


class Conversation(models.Model):
    participant_1 = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_1'
    )
    participant_2 = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_2'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant_1} & {self.participant_2}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ("sms", "SMS"),
        ("mms", "MMS"),
        ("email", "Email"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    body = models.TextField()
    attachments = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField()

    provider = models.CharField(max_length=50)
    provider_message_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
