from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("api/notifications/", views.notifications_api, name="notifications_api"),
    path("api/notifications/read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("api/recommendations/", views.recommendation_api, name="recommendation_api"),
    path("", views.home, name="home"),
    path("shop/", views.product_list, name="product_list"),
    path("category/<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("product/<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("review/add/<int:product_id>/", views.add_review, name="add_review"),
]
