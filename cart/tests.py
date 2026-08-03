from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from store.models import Category, Product
from .cart import Cart
from .models import Coupon

class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Books", slug="books")
        self.product = Product.objects.create(
            category=category,
            name="Book",
            slug="book",
            price=Decimal("1000.00"),
            stock=5,
        )

    def test_cart_add(self):
        request = self.client.request().wsgi_request
        request.session = self.client.session
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        self.assertEqual(len(cart), 2)

    def test_coupon_model(self):
        now = timezone.now()
        coupon = Coupon.objects.create(
            code="TEST10",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=10,
        )
        self.assertEqual(coupon.discount, 10)
