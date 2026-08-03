import math
from collections import defaultdict

from django.db.models import (
    Avg,
    Count,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from .models import Product, RecentlyViewed


def get_recommendations(request, limit=8, exclude_ids=None):
    """Return explainable hybrid recommendations without an external API.

    The score blends purchase/category affinity, wishlist and browsing signals,
    ratings, sales popularity, freshness and merchandising signals.
    """

    exclude_ids = set(exclude_ids or [])
    category_affinity = defaultdict(float)
    wishlist_ids = set()
    from orders.models import OrderItem

    if request.user.is_authenticated:
        purchased = (
            OrderItem.objects.filter(order__user=request.user)
            .exclude(order__status="cancelled")
            .values("product__category_id")
            .annotate(total=Sum("quantity"))
        )
        for row in purchased:
            category_affinity[row["product__category_id"]] += float(row["total"] or 0) * 2.5

        wishlist = request.user.wishlist_items.values_list(
            "product_id",
            "product__category_id",
        )
        for product_id, category_id in wishlist:
            wishlist_ids.add(product_id)
            category_affinity[category_id] += 1.8

        recent = RecentlyViewed.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        recent = RecentlyViewed.objects.filter(session_key=request.session.session_key)

    for row in recent.values("product__category_id")[:20]:
        category_affinity[row["product__category_id"]] += 0.8

    sales_subquery = (
        OrderItem.objects.filter(product_id=OuterRef("pk"))
        .exclude(order__status="cancelled")
        .values("product_id")
        .annotate(total=Sum("quantity"))
        .values("total")[:1]
    )
    products = list(
        Product.objects.filter(available=True, stock__gt=0)
        .exclude(id__in=exclude_ids)
        .select_related("category")
        .annotate(
            calculated_rating=Coalesce(
                Avg("reviews__rating"),
                Value(0.0),
                output_field=FloatField(),
            ),
            calculated_review_count=Count("reviews", distinct=True),
            units_sold=Coalesce(
                Subquery(sales_subquery, output_field=IntegerField()),
                0,
            ),
        )
    )

    scored = []
    for product in products:
        score = category_affinity[product.category_id]
        score += float(product.calculated_rating or 0) * 0.75
        score += math.log1p(product.units_sold or 0) * 1.6
        score += min(product.calculated_review_count, 20) * 0.08
        score += 1.1 if product.featured else 0
        score += 0.7 if product.id in wishlist_ids else 0

        if category_affinity[product.category_id] > 0:
            reason = f"Matches your interest in {product.category.name}"
        elif product.units_sold:
            reason = "Popular with SwiftCart shoppers"
        elif product.calculated_rating:
            reason = "Recommended from customer ratings"
        else:
            reason = "Fresh pick from our catalogue"
        product.recommendation_reason = reason
        scored.append((score, product.id, product))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in scored[:limit]]
