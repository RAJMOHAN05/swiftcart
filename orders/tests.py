from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from store.models import Category, Notification, Product

from .models import Order, OrderItem


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OrderFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="StrongPass123",
        )
        category = Category.objects.create(name="Audio", slug="audio")
        self.product = Product.objects.create(
            category=category,
            name="Studio Headphones",
            slug="studio-headphones",
            price=Decimal("2499.00"),
            stock=4,
            available=True,
        )
        self.client.force_login(self.user)

    def test_order_has_tracking_number_and_initial_event(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Buyer One",
            email="buyer@example.com",
            phone="9999999999",
            address="1 Test Street",
            city="Kolkata",
            postal_code="700001",
            subtotal=Decimal("2499.00"),
            total=Decimal("2499.00"),
        )
        self.assertTrue(order.tracking_number.startswith("SWC"))
        self.assertEqual(order.status_events.count(), 1)
        self.assertEqual(order.status_events.first().status, "placed")

    def test_checkout_sends_email_and_creates_notification(self):
        self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"quantity": 1, "override": False},
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("orders:order_create"),
                {
                    "full_name": "Buyer One",
                    "email": "buyer@example.com",
                    "phone": "9999999999",
                    "address": "1 Test Street",
                    "city": "Kolkata",
                    "postal_code": "700001",
                    "payment_method": "cod",
                    "transaction_reference": "",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(Notification.objects.filter(user=self.user).exists())

    def test_upi_utr_is_saved_and_visible_to_admin(self):
        utr = "426718390245"
        self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"quantity": 1, "override": False},
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("orders:order_create"),
                {
                    "full_name": "Buyer One",
                    "email": "buyer@example.com",
                    "phone": "9999999999",
                    "address": "1 Test Street",
                    "city": "Kolkata",
                    "postal_code": "700001",
                    "payment_method": "upi",
                    "transaction_reference": utr,
                },
            )
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.payment_method, "upi")
        self.assertEqual(order.transaction_reference, utr)

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(self.user)
        changelist = self.client.get(reverse("admin:orders_order_changelist"))
        self.assertContains(changelist, "UTR / Reference")
        self.assertContains(changelist, utr)

        report = self.client.get(reverse("accounts:sales_report"))
        self.assertContains(report, utr)

    def test_invoice_download_is_pdf_and_private(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Buyer One",
            email="buyer@example.com",
            phone="9999999999",
            address="1 Test Street",
            city="Kolkata",
            postal_code="700001",
            subtotal=Decimal("2499.00"),
            total=Decimal("2499.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )
        response = self.client.get(reverse("orders:invoice_pdf", args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

        other = User.objects.create_user(username="other", password="StrongPass123")
        self.client.force_login(other)
        response = self.client.get(reverse("orders:invoice_pdf", args=[order.id]))
        self.assertEqual(response.status_code, 404)

    def test_status_change_creates_real_time_notification(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Buyer One",
            email="buyer@example.com",
            phone="9999999999",
            address="1 Test Street",
            city="Kolkata",
            postal_code="700001",
            subtotal=Decimal("2499.00"),
            total=Decimal("2499.00"),
        )
        with self.captureOnCommitCallbacks(execute=True):
            order.status = "shipped"
            order.save()
        self.assertEqual(order.status_events.last().status, "shipped")
        self.assertTrue(
            Notification.objects.filter(user=self.user, title__contains="updated").exists()
        )
