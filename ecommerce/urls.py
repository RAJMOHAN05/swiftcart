from django.contrib import admin
from django.urls import include, path
from .views import health_check, offline, service_worker

admin.site.site_header = "SwiftCart Control Center"
admin.site.site_title = "SwiftCart Admin"
admin.site.index_title = "Commerce operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("service-worker.js", service_worker, name="service_worker"),
    path("offline/", offline, name="offline"),
    path("", include("store.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("accounts/", include("accounts.urls")),
    path("support/", include("support.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]
