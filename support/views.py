from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from store.models import Notification, Product

from .models import ChatMessage, Conversation


def _conversation_for(request):
    if not request.session.session_key:
        request.session.create()

    if request.user.is_authenticated:
        conversation = Conversation.objects.filter(
            user=request.user,
            status="open",
        ).first()
        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                session_key=request.session.session_key,
            )
        elif not conversation.session_key:
            conversation.session_key = request.session.session_key
            conversation.save(update_fields=["session_key", "updated_at"])
        return conversation

    conversation = Conversation.objects.filter(
        session_key=request.session.session_key,
        status="open",
    ).first()
    if conversation:
        return conversation
    return Conversation.objects.create(session_key=request.session.session_key)


def _assistant_answer(request, message):
    text = message.lower()
    if "order" in text or "track" in text or "delivery" in text:
        if request.user.is_authenticated:
            order = request.user.orders.first()
            if order:
                return (
                    f"Your latest order #{order.id} is {order.get_status_display().lower()}. "
                    f"Tracking ID: {order.tracking_number}. Open My Orders for the full timeline."
                )
        return "Log in and open My Orders to see the live tracking timeline for every purchase."
    if "return" in text or "refund" in text:
        return (
            "Unused products can be returned in their original packaging. "
            "Share your order number here and a support agent can help."
        )
    if "payment" in text or "upi" in text or "cod" in text:
        return "SwiftCart supports Cash on Delivery and UPI at checkout. Never share your UPI PIN."
    if "popular" in text or "recommend" in text or "product" in text:
        names = list(
            Product.objects.filter(available=True, stock__gt=0)
            .order_by("-featured", "-created_at")
            .values_list("name", flat=True)[:3]
        )
        if names:
            return f"Popular right now: {', '.join(names)}. Open Shop to compare prices and ratings."
    return (
        "Thanks—your message is saved for the support team. "
        "I can also help with tracking, returns, payments and product recommendations."
    )


def _serialize_messages(conversation):
    return [
        {
            "id": message.id,
            "sender": message.sender,
            "sender_label": message.get_sender_display(),
            "body": message.body,
            "created_at": message.created_at.strftime("%I:%M %p"),
        }
        for message in conversation.messages.all().order_by("-created_at")[:50][::-1]
    ]


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def chat_api(request):
    conversation = _conversation_for(request)

    if request.method == "POST":
        body = request.POST.get("message", "").strip()
        if not body:
            return JsonResponse({"error": "Please enter a message."}, status=400)
        if len(body) > 1200:
            return JsonResponse({"error": "Message is too long."}, status=400)

        ChatMessage.objects.create(
            conversation=conversation,
            sender="customer",
            user=request.user if request.user.is_authenticated else None,
            body=body,
        )
        ChatMessage.objects.create(
            conversation=conversation,
            sender="assistant",
            body=_assistant_answer(request, body),
        )
        conversation.save(update_fields=["updated_at"])

    return JsonResponse(
        {
            "conversation_id": conversation.id,
            "status": conversation.status,
            "messages": _serialize_messages(conversation),
        }
    )


@staff_member_required
def support_inbox(request):
    conversations = Conversation.objects.select_related("user").prefetch_related(
        Prefetch("messages", queryset=ChatMessage.objects.order_by("-created_at"))
    )
    active_id = request.GET.get("conversation")
    active = None
    if active_id:
        active = get_object_or_404(conversations, id=active_id)
    elif conversations.exists():
        active = conversations.first()
    return render(
        request,
        "support/inbox.html",
        {"conversations": conversations, "active": active},
    )


@staff_member_required
@require_POST
def agent_reply(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    body = request.POST.get("message", "").strip()
    if body:
        ChatMessage.objects.create(
            conversation=conversation,
            sender="agent",
            user=request.user,
            body=body[:1200],
        )
        conversation.status = "open"
        conversation.save(update_fields=["status", "updated_at"])
        if conversation.user:
            Notification.objects.create(
                user=conversation.user,
                title="Support replied",
                message=body[:255],
                icon="bi-chat-heart",
            )
    return redirect(f"/support/inbox/?conversation={conversation.id}")


@staff_member_required
@require_POST
def close_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    conversation.status = "closed"
    conversation.save(update_fields=["status", "updated_at"])
    return redirect("support:inbox")
