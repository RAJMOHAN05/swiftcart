from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from orders.models import Order, OrderItem
from .models import Category, Product, Review, WishlistItem

class StoreTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics", slug="electronics", icon="🎧"
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Test Phone",
            slug="test-phone",
            price=Decimal("999.00"),
            original_price=Decimal("1199.00"),
            stock=5,
            featured=True,
            available=True,
        )
        self.user = User.objects.create_user(username="raj", password="StrongPass123")

    def create_order_with_product(self, status="placed"):
        order = Order.objects.create(
            user=self.user,
            full_name="Raj Mohan",
            email="raj@example.com",
            phone="9999999999",
            address="1 Test Street",
            city="Kolkata",
            postal_code="700001",
            subtotal=self.product.price,
            total=self.product.price,
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )
        return order

    def test_home_page(self):
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Phone")

    def test_discount_percentage(self):
        self.assertEqual(self.product.discount_percentage, 17)

    def test_wishlist_requires_login(self):
        response = self.client.get(reverse("store:wishlist"))
        self.assertEqual(response.status_code, 302)

    def test_review_average(self):
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Excellent",
            comment="Excellent product.",
        )
        self.assertEqual(self.product.average_rating, 5.0)

    def test_review_is_blocked_without_a_delivered_purchase(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("store:add_review", args=[self.product.id]),
            {"rating": 5, "title": "Great", "comment": "A useful product."},
        )
        self.assertRedirects(
            response,
            f"{self.product.get_absolute_url()}#reviews",
            fetch_redirect_response=False,
        )
        self.assertFalse(Review.objects.filter(user=self.user, product=self.product).exists())

    def test_placed_order_does_not_unlock_review_form(self):
        self.create_order_with_product(status="placed")
        self.client.force_login(self.user)
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "Available after delivery")
        self.assertNotContains(response, "Publish review")

    def test_delivered_purchase_unlocks_and_creates_verified_review(self):
        order = self.create_order_with_product(status="delivered")
        self.product.available = False
        self.product.stock = 0
        self.product.save(update_fields=["available", "stock"])
        self.client.force_login(self.user)
        detail = self.client.get(self.product.get_absolute_url())
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Publish review")

        order_detail = self.client.get(reverse("orders:order_detail", args=[order.id]))
        self.assertContains(order_detail, "Write review")

        response = self.client.post(
            reverse("store:add_review", args=[self.product.id]),
            {"rating": 5, "title": "Excellent", "comment": "Delivered and tested."},
        )
        self.assertRedirects(response, self.product.get_absolute_url())
        review = Review.objects.get(user=self.user, product=self.product)
        self.assertTrue(review.verified_purchase)

    def test_verified_purchase_requires_delivered_status(self):
        order = self.create_order_with_product(status="shipped")
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title="Still waiting",
            comment="Not delivered yet.",
        )
        self.assertFalse(review.verified_purchase)
        order.status = "delivered"
        order.save()
        self.assertTrue(review.verified_purchase)

    def test_advanced_price_and_stock_filters(self):
        response = self.client.get(
            reverse("store:product_list"),
            {"min_price": "900", "max_price": "1000", "in_stock": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Phone")

    def test_ajax_wishlist_toggle(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("store:toggle_wishlist", args=[self.product.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["active"])
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)

    def test_recommendation_api_is_explainable(self):
        response = self.client.get(reverse("store:recommendation_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["engine"], "hybrid-affinity-v1")
        self.assertIn("reason", payload["items"][0])

    def test_catalogue_uses_isolated_responsive_filter_styles(self):
        response = self.client.get(reverse("store:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/catalogue-v2.css")
        self.assertContains(response, 'id="mobileFilterToggle"')
        self.assertContains(response, 'id="catalogueFilterPanel"')
        with open("static/css/catalogue-v2.css", encoding="utf-8") as stylesheet:
            css = stylesheet.read()
        self.assertIn(
            ".advanced-filter-form .filter-input-icon>input{padding-left:48px!important}",
            css,
        )

    def test_dark_mode_contrast_patch_is_present(self):
        response = self.client.get(reverse("store:product_list"))
        self.assertContains(response, "20260731.6")
        with open("static/css/style.css", encoding="utf-8") as stylesheet:
            css = stylesheet.read()
        self.assertIn('html[data-theme="dark"] .page-hero', css)
        self.assertIn('html[data-theme="dark"] .review-access-state', css)
        with open("static/css/catalogue-v2.css", encoding="utf-8") as stylesheet:
            catalogue_css = stylesheet.read()
        self.assertIn('html[data-theme="dark"] .filter-check', catalogue_css)

    def test_pwa_install_fallback_and_cache_upgrade_are_present(self):
        response = self.client.get(reverse("store:home"))
        self.assertContains(response, 'id="installAppButton"')
        self.assertContains(response, 'id="installHelpModal"')
        self.assertContains(response, "20260731.6")
        worker = self.client.get(reverse("service_worker"))
        self.assertEqual(worker.status_code, 200)
        self.assertContains(worker, "swiftcart-phase2-v6")
        self.assertContains(worker, "networkFirst")
