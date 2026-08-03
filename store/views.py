from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, FloatField, Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from cart.forms import CartAddProductForm

from .forms import ReviewForm
from .models import Category, Product, RecentlyViewed, Review, WishlistItem
from .recommendations import get_recommendations


def _has_delivered_purchase(user, product):
    """Only customers who received this product may publish a review."""
    return user.is_authenticated and product.order_items.filter(
        order__user=user,
        order__status="delivered",
    ).exists()


def _catalogue(available_only=True):
    products = Product.objects.all()
    if available_only:
        products = products.filter(available=True)
    return (
        products
        .select_related("category")
        .annotate(
            calculated_rating=Coalesce(
                Avg("reviews__rating"),
                Value(0.0),
                output_field=FloatField(),
            ),
            calculated_review_count=Count("reviews", distinct=True),
        )
    )


def _decimal_filter(value):
    try:
        return Decimal(value) if value else None
    except (InvalidOperation, TypeError):
        return None


def _remember_product(request, product):
    if not request.session.session_key:
        request.session.save()

    lookup = {"product": product}
    if request.user.is_authenticated:
        lookup["user"] = request.user
        lookup["session_key"] = ""
    else:
        lookup["user"] = None
        lookup["session_key"] = request.session.session_key

    RecentlyViewed.objects.update_or_create(**lookup, defaults={})
    recent = RecentlyViewed.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        session_key="" if request.user.is_authenticated else request.session.session_key,
    ).order_by("-viewed_at")
    stale_ids = list(recent.values_list("id", flat=True)[30:])
    if stale_ids:
        RecentlyViewed.objects.filter(id__in=stale_ids).delete()


def home(request):
    featured_products = _catalogue().filter(featured=True)[:8]
    new_products = _catalogue().order_by("-created_at")[:8]
    recommended_products = get_recommendations(request, limit=4)
    return render(
        request,
        "store/home.html",
        {
            "categories": Category.objects.all(),
            "featured_products": featured_products,
            "new_products": new_products,
            "recommended_products": recommended_products,
            "flash_sale_end": timezone.now() + timedelta(hours=8),
        },
    )


def product_list(request, category_slug=None):
    category = None
    products = _catalogue()
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "newest")
    min_price = _decimal_filter(request.GET.get("min_price"))
    max_price = _decimal_filter(request.GET.get("max_price"))
    min_rating = _decimal_filter(request.GET.get("rating"))
    in_stock = request.GET.get("in_stock") == "1"

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
        selected_category = category.slug
    elif selected_category:
        category = Category.objects.filter(slug=selected_category).first()
        if category:
            products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(badge__icontains=query)
        )
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)
    if min_rating is not None:
        products = products.filter(calculated_rating__gte=min_rating)
    if in_stock:
        products = products.filter(stock__gt=0)

    sort_options = {
        "newest": "-created_at",
        "price_low": "price",
        "price_high": "-price",
        "name": "name",
        "rating": "-calculated_rating",
        "popular": "-calculated_review_count",
    }
    products = products.order_by(sort_options.get(sort, "-created_at"), "-id")
    page_obj = Paginator(products, 12).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "store/product/list.html",
        {
            "category": category,
            "categories": Category.objects.all(),
            "products": page_obj,
            "page_obj": page_obj,
            "query": query,
            "sort": sort,
            "selected_category": selected_category,
            "min_price": request.GET.get("min_price", ""),
            "max_price": request.GET.get("max_price", ""),
            "min_rating": request.GET.get("rating", ""),
            "in_stock": in_stock,
            "querystring": query_params.urlencode(),
        },
    )


def product_detail(request, id, slug):
    # Keep purchased products reachable after stock reaches zero so a delivered
    # customer can still open the product page and submit their review.
    product = get_object_or_404(_catalogue(available_only=False), id=id, slug=slug)
    _remember_product(request, product)

    related_products = (
        _catalogue()
        .filter(category=product.category)
        .exclude(id=product.id)
        .order_by("-calculated_rating", "-featured")[:4]
    )
    if request.user.is_authenticated:
        recent_rows = RecentlyViewed.objects.filter(user=request.user)
    else:
        recent_rows = RecentlyViewed.objects.filter(session_key=request.session.session_key)
    recent_ids = list(
        recent_rows.exclude(product=product).values_list("product_id", flat=True)[:4]
    )
    recently_viewed = list(_catalogue().filter(id__in=recent_ids))
    recently_viewed.sort(key=lambda item: recent_ids.index(item.id))

    user_has_reviewed = False
    can_review = False
    in_wishlist = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(product=product, user=request.user).exists()
        can_review = not user_has_reviewed and _has_delivered_purchase(request.user, product)
        in_wishlist = WishlistItem.objects.filter(product=product, user=request.user).exists()

    return render(
        request,
        "store/product/detail.html",
        {
            "product": product,
            "related_products": related_products,
            "recently_viewed": recently_viewed,
            "cart_product_form": CartAddProductForm(),
            "review_form": ReviewForm(),
            "user_has_reviewed": user_has_reviewed,
            "can_review": can_review,
            "in_wishlist": in_wishlist,
        },
    )


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "active": created,
                "count": request.user.wishlist_items.count(),
                "message": (
                    f"{product.name} added to your wishlist."
                    if created
                    else f"{product.name} removed from your wishlist."
                ),
            }
        )

    if created:
        messages.success(request, f"{product.name} added to your wishlist.")
    else:
        messages.info(request, f"{product.name} removed from your wishlist.")
    return redirect(request.POST.get("next") or product.get_absolute_url())


@login_required
def wishlist(request):
    items = request.user.wishlist_items.select_related("product", "product__category")
    return render(request, "store/wishlist.html", {"items": items})


@login_required
@require_POST
def add_review(request, product_id):
    # Availability controls new sales, not review eligibility for past orders.
    product = get_object_or_404(Product, id=product_id)
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "You have already reviewed this product.")
        return redirect(product.get_absolute_url())

    if not _has_delivered_purchase(request.user, product):
        messages.warning(
            request,
            "You can review this product after your order has been delivered.",
        )
        return redirect(f"{product.get_absolute_url()}#reviews")

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, "Your review has been published.")
    else:
        messages.error(request, "Please correct the review form.")
    return redirect(product.get_absolute_url())


@login_required
def notifications_api(request):
    items = request.user.notifications.all()[:10]
    return JsonResponse(
        {
            "count": request.user.notifications.filter(is_read=False).count(),
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "message": item.message,
                    "icon": item.icon,
                    "url": item.url,
                    "created_at": item.created_at.strftime("%d %b, %I:%M %p"),
                    "is_read": item.is_read,
                }
                for item in items
            ],
        }
    )


@login_required
@require_POST
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})


def recommendation_api(request):
    products = get_recommendations(request, limit=6)
    return JsonResponse(
        {
            "engine": "hybrid-affinity-v1",
            "items": [
                {
                    "name": product.name,
                    "price": str(product.price),
                    "image": product.image_url,
                    "url": product.get_absolute_url(),
                    "badge": product.badge,
                    "reason": product.recommendation_reason,
                }
                for product in products
            ],
        }
    )
