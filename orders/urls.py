from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.order_create, name="order_create"),
    path("history/", views.order_history, name="order_history"),
    path("<int:order_id>/invoice/", views.invoice_pdf, name="invoice_pdf"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
]
