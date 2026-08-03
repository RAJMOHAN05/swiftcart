from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem, OrderStatusEvent

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]
    extra = 0


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    readonly_fields = ["created_at"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id", "full_name", "total", "payment_method", "utr_reference",
        "status", "paid", "tracking_number", "created_at",
    ]
    list_filter = ["status", "paid", "payment_method", "created_at"]
    list_editable = ["status", "paid"]
    list_display_links = ["id", "full_name"]
    search_fields = [
        "full_name", "email", "phone", "coupon_code",
        "transaction_reference", "tracking_number",
    ]
    readonly_fields = ["tracking_number", "created_at", "updated_at"]
    inlines = [OrderItemInline, OrderStatusEventInline]
    date_hierarchy = "created_at"
    list_per_page = 30
    fieldsets = (
        (
            "Customer & delivery",
            {"fields": ("user", "full_name", "email", "phone", "address", "city", "postal_code")},
        ),
        (
            "Payment verification",
            {
                "fields": (
                    ("payment_method", "transaction_reference"),
                    ("subtotal", "discount", "total"),
                    ("coupon_code", "paid"),
                ),
                "description": "For UPI orders, verify the customer-submitted UTR / transaction reference before marking the payment as paid.",
            },
        ),
        (
            "Fulfilment",
            {"fields": (("status", "estimated_delivery"), "tracking_number")},
        ),
        (
            "Audit information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="UTR / Reference", ordering="transaction_reference")
    def utr_reference(self, obj):
        if obj.payment_method != "upi":
            return format_html('<span class="utr-empty">{}</span>', "Not applicable")
        if not obj.transaction_reference:
            return format_html('<span class="utr-missing">{}</span>', "Missing")
        return format_html(
            '<span class="utr-reference">{}</span>',
            obj.transaction_reference,
        )


@admin.register(OrderStatusEvent)
class OrderStatusEventAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "location", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order__tracking_number", "note", "location"]
