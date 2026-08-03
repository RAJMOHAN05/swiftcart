import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from orders.models import Order, OrderItem
from store.models import Product

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    return render(
        request,
        "accounts/dashboard.html",
        {
            "recent_orders": request.user.orders.prefetch_related("items")[:5],
            "wishlist_items": request.user.wishlist_items.select_related("product")[:4],
        },
    )


def _date_range(request, default_days=30):
    today = timezone.localdate()
    start = parse_date(request.GET.get("start", "")) or today - timedelta(days=default_days - 1)
    end = parse_date(request.GET.get("end", "")) or today
    if start > end:
        start, end = end, start
    if (end - start).days > 365:
        start = end - timedelta(days=365)
    return start, end


@staff_member_required
def seller_dashboard(request):
    start, end = _date_range(request)
    orders = Order.objects.filter(created_at__date__range=(start, end))
    completed = orders.exclude(status="cancelled")
    revenue = completed.aggregate(total=Sum("total"))["total"] or 0
    order_count = orders.count()
    average_order = completed.aggregate(total=Sum("total"))["total"] or 0
    average_order = average_order / completed.count() if completed.count() else 0

    period_days = (end - start).days + 1
    previous_start = start - timedelta(days=period_days)
    previous_end = start - timedelta(days=1)
    previous_revenue = (
        Order.objects.filter(created_at__date__range=(previous_start, previous_end))
        .exclude(status="cancelled")
        .aggregate(total=Sum("total"))["total"]
        or 0
    )
    if previous_revenue:
        revenue_growth = float((revenue - previous_revenue) * 100 / previous_revenue)
    else:
        revenue_growth = 100.0 if revenue else 0.0

    revenue_data = list(
        completed.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total"), orders=Count("id"))
        .order_by("day")
    )
    for row in revenue_data:
        row["day"] = row["day"].isoformat()

    category_sales = list(
        OrderItem.objects.filter(
            order__created_at__date__range=(start, end)
        )
        .exclude(order__status="cancelled")
        .values("product__category__name")
        .annotate(
            revenue=Sum(
                F("price") * F("quantity"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by("-revenue")[:8]
    )
    context = {
        "start": start,
        "end": end,
        "revenue": revenue,
        "revenue_growth": revenue_growth,
        "average_order": average_order,
        "orders_count": order_count,
        "customers_count": completed.values("user").distinct().count(),
        "products_count": Product.objects.count(),
        "low_stock": Product.objects.filter(stock__lte=5).order_by("stock")[:8],
        "recent_orders": orders.select_related("user").order_by("-created_at")[:8],
        "status_data": list(
            orders.values("status").annotate(total=Count("id")).order_by("status")
        ),
        "top_products": list(
            OrderItem.objects.filter(order__created_at__date__range=(start, end))
            .exclude(order__status="cancelled")
            .values("product__name")
            .annotate(quantity=Sum("quantity"))
            .order_by("-quantity")[:6]
        ),
        "revenue_data": revenue_data,
        "category_sales": category_sales,
    }
    return render(request, "accounts/seller_dashboard.html", context)


@staff_member_required
def sales_report(request):
    start, end = _date_range(request)
    orders = (
        Order.objects.filter(created_at__date__range=(start, end))
        .select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")
    )
    revenue = orders.exclude(status="cancelled").aggregate(total=Sum("total"))["total"] or 0

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="swiftcart-sales-{start}-{end}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Order ID",
                "Date",
                "Customer",
                "Email",
                "Status",
                "Payment",
                "UTR / Transaction Reference",
                "Items",
                "Subtotal",
                "Discount",
                "Revenue",
                "Tracking ID",
            ]
        )
        for order in orders:
            writer.writerow(
                [
                    order.id,
                    timezone.localtime(order.created_at).strftime("%Y-%m-%d %H:%M"),
                    order.full_name,
                    order.email,
                    order.get_status_display(),
                    order.get_payment_method_display(),
                    order.transaction_reference,
                    sum(item.quantity for item in order.items.all()),
                    order.subtotal,
                    order.discount,
                    0 if order.status == "cancelled" else order.total,
                    order.tracking_number,
                ]
            )
        writer.writerow([])
        writer.writerow(["TOTAL REVENUE", "", "", "", "", "", "", "", "", "", revenue, ""])
        return response

    return render(
        request,
        "accounts/sales_report.html",
        {
            "orders": orders,
            "start": start,
            "end": end,
            "revenue": revenue,
            "orders_count": orders.count(),
            "delivered_count": orders.filter(status="delivered").count(),
            "cancelled_count": orders.filter(status="cancelled").count(),
        },
    )
