from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order


class AdminReportingTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="manager",
            password="StrongPass123",
            is_staff=True,
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            password="StrongPass123",
        )
        Order.objects.create(
            user=self.buyer,
            full_name="Buyer",
            email="buyer@example.com",
            phone="9999999999",
            address="Test Street",
            city="Delhi",
            postal_code="110001",
            subtotal=Decimal("1500.00"),
            total=Decimal("1500.00"),
        )

    def test_analytics_requires_staff(self):
        response = self.client.get(reverse("accounts:seller_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("accounts:seller_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analytics dashboard")

    def test_csv_sales_report(self):
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("accounts:sales_report"),
            {"format": "csv"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(b"TOTAL REVENUE", response.content)
        self.assertIn(b"UTR / Transaction Reference", response.content)

    def test_modern_admin_branding_and_styles_load(self):
        self.staff.is_superuser = True
        self.staff.save(update_fields=["is_superuser"])
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Commerce Control Center")
        self.assertContains(response, "admin-modern.css")
        self.assertContains(response, "Manage orders")
