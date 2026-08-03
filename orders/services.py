from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


def _order_url(order, request=None):
    path = reverse("orders:order_detail", args=[order.id])
    if request:
        return request.build_absolute_uri(path)
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def send_order_confirmation(order, request=None):
    context = {"order": order, "order_url": _order_url(order, request)}
    subject = f"SwiftCart order #{order.id} confirmed"
    text = render_to_string("emails/order_confirmation.txt", context)
    html = render_to_string("emails/order_confirmation.html", context)
    email = EmailMultiAlternatives(
        subject,
        text,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
    email.attach_alternative(html, "text/html")
    return email.send(fail_silently=True)


def send_order_status_update(order):
    context = {"order": order, "order_url": _order_url(order)}
    subject = f"Order #{order.id}: {order.get_status_display()}"
    text = render_to_string("emails/order_status.txt", context)
    html = render_to_string("emails/order_status.html", context)
    email = EmailMultiAlternatives(
        subject,
        text,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
    email.attach_alternative(html, "text/html")
    return email.send(fail_silently=True)
