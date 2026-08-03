from .models import Category

def store_navigation(request):
    wishlist_count = 0
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_count = request.user.wishlist_items.count()
        wishlist_product_ids = list(
            request.user.wishlist_items.values_list("product_id", flat=True)
        )
    notification_count = 0
    if request.user.is_authenticated:
        notification_count = request.user.notifications.filter(is_read=False).count()
    return {
        "nav_categories": Category.objects.all()[:6],
        "wishlist_count": wishlist_count,
        "wishlist_product_ids": wishlist_product_ids,
        "notification_count": notification_count,
    }
