from decimal import Decimal
from django.conf import settings
from store.models import Product
from .models import Coupon

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get(settings.CART_COUPON_ID)

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}
        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys())
        cart_copy = self.cart.copy()

        for product in products:
            item = cart_copy[str(product.id)]
            item["product"] = product
            item["price"] = product.price

        from .forms import CartAddProductForm
        for item in cart_copy.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            item["update_quantity_form"] = CartAddProductForm(
                initial={"quantity": item["quantity"], "override": True}
            )
            yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def coupon(self):
        if self.coupon_id:
            return Coupon.objects.filter(id=self.coupon_id, active=True).first()
        return None

    def get_subtotal(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )

    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_subtotal()
        return Decimal(0)

    def get_total_price(self):
        return self.get_subtotal() - self.get_discount()

    def clear(self):
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.pop(settings.CART_COUPON_ID, None)
        self.save()
