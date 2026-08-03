from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("api/chat/", views.chat_api, name="chat_api"),
    path("inbox/", views.support_inbox, name="inbox"),
    path("inbox/<int:conversation_id>/reply/", views.agent_reply, name="agent_reply"),
    path("inbox/<int:conversation_id>/close/", views.close_conversation, name="close"),
]

