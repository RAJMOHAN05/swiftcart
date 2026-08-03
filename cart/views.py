from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from store.models import Product
from .cart import Cart
from .forms import CartAddProductForm, CouponApplyForm
from .models import Coupon

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} units are available.")
        else:
            cart.add(
                product=product,
                quantity=quantity,
                override_quantity=form.cleaned_data["override"],
            )
            messages.success(request, f"{product.name} added to cart.")
    return redirect("cart:cart_detail")

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} removed from cart.")
    return redirect("cart:cart_detail")

def cart_detail(request):
    return render(
        request,
        "cart/detail.html",
        {"cart": Cart(request), "coupon_form": CouponApplyForm()},
    )

@require_POST
def coupon_apply(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    request.session[settings.CART_COUPON_ID] = None
    if form.is_valid():
        code = form.cleaned_data["code"].strip()
        coupon = Coupon.objects.filter(
            code__iexact=code,
            valid_from__lte=now,
            valid_to__gte=now,
            active=True,
        ).first()
        if coupon:
            request.session[settings.CART_COUPON_ID] = coupon.id
            messages.success(request, f"Coupon {coupon.code} applied.")
        else:
            messages.error(request, "This coupon is invalid or expired.")
    return redirect("cart:cart_detail")
