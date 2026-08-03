from django.contrib import admin

from .models import ChatMessage, Conversation


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["sender", "user", "body", "created_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "subject", "status", "updated_at"]
    list_filter = ["status", "updated_at"]
    search_fields = ["user__username", "subject", "messages__body"]
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "user", "created_at"]
    list_filter = ["sender", "created_at"]
    search_fields = ["body", "user__username"]

