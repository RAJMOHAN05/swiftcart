from django.conf import settings
from django.db import models


class Conversation(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("closed", "Closed")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="support_conversations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=80, blank=True, db_index=True)
    subject = models.CharField(max_length=160, default="Shopping support")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        customer = self.user.username if self.user else self.session_key[:10]
        return f"{customer} — {self.get_status_display()}"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ("customer", "Customer"),
        ("assistant", "SwiftCart Assistant"),
        ("agent", "Support Agent"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    sender = models.CharField(max_length=12, choices=SENDER_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    body = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_sender_display()}: {self.body[:50]}"

