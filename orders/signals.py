from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from store.models import Notification

from .models import Order, OrderStatusEvent
from .services import send_order_status_update


STATUS_NOTES = {
    "placed": "We received your order.",
    "confirmed": "Payment and order details were confirmed.",
    "packed": "Your items were packed and quality checked.",
    "shipped": "The package left our fulfilment centre.",
    "delivered": "The package was delivered successfully.",
    "cancelled": "This order was cancelled.",
}


@receiver(pre_save, sender=Order)
def remember_previous_status(sender, instance, **kwargs):
    instance._previous_status = None
    if instance.pk:
        instance._previous_status = (
            sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )


@receiver(post_save, sender=Order)
def create_tracking_event(sender, instance, created, **kwargs):
    status_changed = created or instance._previous_status != instance.status
    if not status_changed:
        return

    OrderStatusEvent.objects.create(
        order=instance,
        status=instance.status,
        note=STATUS_NOTES.get(instance.status, instance.get_status_display()),
        location="SwiftCart fulfilment centre" if instance.status != "delivered" else instance.city,
    )
    if not created:
        Notification.objects.create(
            user=instance.user,
            title=f"Order #{instance.id} updated",
            message=STATUS_NOTES.get(instance.status, instance.get_status_display()),
            icon="bi-box-seam",
            url=reverse("orders:order_detail", args=[instance.id]),
        )
        transaction.on_commit(lambda: send_order_status_update(instance))

