from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ChatMessage, Conversation


class SupportChatTests(TestCase):
    def test_anonymous_chat_creates_conversation_and_reply(self):
        response = self.client.post(
            reverse("support:chat_api"),
            {"message": "How can I track my order?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 2)
        self.assertEqual(response.json()["messages"][-1]["sender"], "assistant")

    def test_staff_inbox_is_protected(self):
        response = self.client.get(reverse("support:inbox"))
        self.assertEqual(response.status_code, 302)
        staff = User.objects.create_user(
            username="agent",
            password="StrongPass123",
            is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("support:inbox"))
        self.assertEqual(response.status_code, 200)

