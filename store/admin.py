from django.contrib import admin
from .models import Category, Notification, Product, RecentlyViewed, Review, WishlistItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon"]
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "price", "original_price",
        "stock", "featured", "available",
    ]
    list_filter = ["available", "featured", "category", "created_at"]
    list_editable = ["price", "stock", "featured", "available"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description", "category__name"]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "title", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__name", "user__username", "title"]

@admin.register(WishlistItem)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["user__username", "title", "message"]


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "session_key", "viewed_at"]
    search_fields = ["product__name", "user__username", "session_key"]
