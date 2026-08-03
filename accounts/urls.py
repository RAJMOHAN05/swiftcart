from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/reports/", views.sales_report, name="sales_report"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
