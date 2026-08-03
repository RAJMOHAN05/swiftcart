from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from cart.cart import Cart
from store.models import Notification, Review

from .forms import OrderCreateForm
from .models import Order, OrderItem
from .services import send_order_confirmation


@login_required
@transaction.atomic
def order_create(request):
    cart = Cart(request)

    if len(cart) == 0:
        return render(request, "orders/empty_cart.html")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = cart.get_subtotal()
            order.discount = cart.get_discount()
            order.total = cart.get_total_price()
            order.coupon_code = cart.coupon.code if cart.coupon else ""
            order.save()

            for item in cart:
                product = item["product"]
                if item["quantity"] > product.stock:
                    messages.error(
                        request,
                        f"Not enough stock for {product.name}. Please update your cart.",
                    )
                    transaction.set_rollback(True)
                    return redirect("cart:cart_detail")

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item["price"],
                    quantity=item["quantity"],
                )
                product.stock -= item["quantity"]
                if product.stock == 0:
                    product.available = False
                    product.save(update_fields=["stock", "available"])
                else:
                    product.save(update_fields=["stock"])

            Notification.objects.create(
                user=request.user,
                title=f"Order #{order.id} confirmed",
                message=f"We received your order. Tracking ID: {order.tracking_number}",
                icon="bi-bag-check",
                url=reverse("orders:order_detail", args=[order.id]),
            )
            transaction.on_commit(lambda: send_order_confirmation(order, request))
            cart.clear()
            return render(request, "orders/created.html", {"order": order})
    else:
        form = OrderCreateForm(
            initial={"email": request.user.email, "payment_method": "cod"}
        )

    return render(request, "orders/create.html", {"cart": cart, "form": form})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related("items__product", "status_events")
    return render(request, "orders/history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product", "status_events"),
        id=order_id,
        user=request.user,
    )
    status_order = [
        ("placed", "Order placed", "bi-receipt"),
        ("confirmed", "Confirmed", "bi-check2-circle"),
        ("packed", "Packed", "bi-box-seam"),
        ("shipped", "Shipped", "bi-truck"),
        ("delivered", "Delivered", "bi-house-check"),
    ]
    status_codes = [item[0] for item in status_order]
    current_step = status_codes.index(order.status) if order.status in status_codes else -1
    events_by_status = {event.status: event for event in order.status_events.all()}
    timeline = [
        {
            "code": code,
            "label": label,
            "icon": icon,
            "complete": index <= current_step,
            "current": index == current_step,
            "event": events_by_status.get(code),
        }
        for index, (code, label, icon) in enumerate(status_order)
    ]
    order_items = list(order.items.all())
    reviewed_product_ids = set(
        Review.objects.filter(
            user=request.user,
            product_id__in=[item.product_id for item in order_items],
        ).values_list("product_id", flat=True)
    )
    for item in order_items:
        item.review_submitted = item.product_id in reviewed_product_ids
        item.can_review = order.status == "delivered" and not item.review_submitted

    return render(
        request,
        "orders/detail.html",
        {
            "order": order,
            "order_items": order_items,
            "timeline": timeline,
            "current_step": current_step,
        },
    )


def _draw_invoice_header(pdf, order, page_width, page_height):
    pdf.setFillColor(colors.HexColor("#101828"))
    pdf.rect(0, page_height - 48 * mm, page_width, 48 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(18 * mm, page_height - 22 * mm, "SwiftCart")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(18 * mm, page_height - 30 * mm, "Premium shopping, delivered simply.")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawRightString(page_width - 18 * mm, page_height - 22 * mm, "TAX INVOICE")
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(
        page_width - 18 * mm,
        page_height - 30 * mm,
        f"Invoice SC-{order.id:06d}",
    )


@login_required
def invoice_pdf(request, order_id):
    orders = Order.objects.prefetch_related("items__product")
    if not request.user.is_staff:
        orders = orders.filter(user=request.user)
    order = get_object_or_404(orders, id=order_id)

    buffer = BytesIO()
    page_width, page_height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"SwiftCart Invoice SC-{order.id:06d}")
    _draw_invoice_header(pdf, order, page_width, page_height)

    y = page_height - 62 * mm
    pdf.setFillColor(colors.HexColor("#344054"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(18 * mm, y, "BILLED TO")
    pdf.drawString(112 * mm, y, "ORDER DETAILS")
    pdf.setFont("Helvetica", 10)
    lines = [
        order.full_name,
        order.address,
        f"{order.city} - {order.postal_code}",
        order.email,
        order.phone,
    ]
    for index, line in enumerate(lines):
        pdf.drawString(18 * mm, y - (7 + index * 5) * mm, str(line)[:65])
    details = [
        f"Order: #{order.id}",
        f"Date: {order.created_at:%d %b %Y}",
        f"Tracking: {order.tracking_number}",
        f"Payment: {order.get_payment_method_display()}",
        f"Status: {order.get_status_display()}",
    ]
    for index, line in enumerate(details):
        pdf.drawString(112 * mm, y - (7 + index * 5) * mm, line)

    y -= 40 * mm
    pdf.setFillColor(colors.HexColor("#EEF2FF"))
    pdf.roundRect(16 * mm, y - 8 * mm, page_width - 32 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#344054"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(20 * mm, y - 4 * mm, "ITEM")
    pdf.drawRightString(145 * mm, y - 4 * mm, "QTY")
    pdf.drawRightString(171 * mm, y - 4 * mm, "PRICE")
    pdf.drawRightString(192 * mm, y - 4 * mm, "TOTAL")
    y -= 15 * mm

    pdf.setFont("Helvetica", 9)
    for item in order.items.all():
        if y < 38 * mm:
            pdf.showPage()
            _draw_invoice_header(pdf, order, page_width, page_height)
            y = page_height - 62 * mm
        pdf.setFillColor(colors.HexColor("#101828"))
        pdf.drawString(20 * mm, y, item.product.name[:52])
        pdf.drawRightString(145 * mm, y, str(item.quantity))
        pdf.drawRightString(171 * mm, y, f"Rs. {item.price:,.2f}")
        pdf.drawRightString(192 * mm, y, f"Rs. {item.get_cost():,.2f}")
        pdf.setStrokeColor(colors.HexColor("#EAECF0"))
        pdf.line(20 * mm, y - 3 * mm, 192 * mm, y - 3 * mm)
        y -= 9 * mm

    y -= 5 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(168 * mm, y, "Subtotal")
    pdf.drawRightString(192 * mm, y, f"Rs. {order.subtotal:,.2f}")
    y -= 7 * mm
    pdf.drawRightString(168 * mm, y, "Discount")
    pdf.drawRightString(192 * mm, y, f"- Rs. {order.discount:,.2f}")
    y -= 9 * mm
    pdf.setFillColor(colors.HexColor("#4F46E5"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawRightString(168 * mm, y, "Grand total")
    pdf.drawRightString(192 * mm, y, f"Rs. {order.total:,.2f}")
    pdf.setFillColor(colors.HexColor("#667085"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(18 * mm, 18 * mm, "Thank you for shopping with SwiftCart.")
    pdf.drawRightString(page_width - 18 * mm, 18 * mm, "Computer-generated invoice")
    pdf.save()

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="swiftcart-invoice-{order.id}.pdf"'
    )
    return response
