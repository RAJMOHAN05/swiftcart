from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from cart.models import Coupon
from store.models import Category, Product

class Command(BaseCommand):
    help = "Create premium demo categories, products and coupon"

    def handle(self, *args, **options):
        categories = {
            "Electronics": ("electronics", "🎧", "Smart gadgets and everyday technology"),
            "Fashion": ("fashion", "👟", "Modern clothing and lifestyle essentials"),
            "Home": ("home", "🏠", "Beautiful products for your living space"),
            "Books": ("books", "📚", "Books for learning and personal growth"),
            "Beauty": ("beauty", "💄", "Skincare, makeup and personal care essentials"),
            "Accessories": ("accessories", "⌚", "Watches, bags and everyday accessories"),
            "Footwear": ("footwear", "👞", "Shoes and footwear for every occasion"),
        }

        category_objects = {}
        for name, (slug, icon, description) in categories.items():
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "icon": icon, "description": description},
            )
            category_objects[name] = category

        products = [
            {
                "category": "Electronics",
                "name": "JBL Tune Wireless Headphones",
                "slug": "jbl-tune-wireless-headphones",
                "short_description": "Premium wireless sound with active noise cancellation.",
                "description": "Enjoy deep bass, clear calls and long battery life in a comfortable premium design.",
                "price": "4999.00",
                "original_price": "6999.00",
                "stock": 22,
                "badge": "Best Seller",
                "featured": True,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Electronics",
                "name": "Noise ColorFit Smart Watch",
                "slug": "noise-colorfit-smart-watch",
                "short_description": "Fitness, calls and notifications on your wrist.",
                "description": "Track health, workouts and daily activity with a bright display and stylish metal body.",
                "price": "5999.00",
                "original_price": "7999.00",
                "stock": 18,
                "badge": "Trending",
                "featured": True,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Fashion",
                "name": "Puma Everyday Running Shoes",
                "slug": "puma-everyday-running-shoes",
                "short_description": "Lightweight comfort for running and everyday wear.",
                "description": "Breathable upper, cushioned sole and a clean streetwear-inspired silhouette.",
                "price": "3299.00",
                "original_price": "4599.00",
                "stock": 30,
                "badge": "New",
                "featured": True,
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Fashion",
                "name": "H&M Relaxed Fit T-Shirt",
                "slug": "hm-relaxed-fit-t-shirt",
                "short_description": "Heavy cotton oversized T-shirt with premium finish.",
                "description": "A minimal everyday T-shirt made for comfort, layering and relaxed styling.",
                "price": "999.00",
                "original_price": "1499.00",
                "stock": 45,
                "badge": "Popular",
                "featured": False,
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Home",
                "name": "Philips Modern Table Lamp",
                "slug": "philips-modern-table-lamp",
                "short_description": "Warm ambient lighting with a clean Scandinavian look.",
                "description": "A modern table lamp ideal for bedrooms, work desks and reading corners.",
                "price": "2199.00",
                "original_price": "2999.00",
                "stock": 16,
                "badge": "Editor Pick",
                "featured": True,
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Home",
                "name": "Home Centre Ceramic Vase",
                "slug": "home-centre-ceramic-vase",
                "short_description": "Hand-finished ceramic decor for modern interiors.",
                "description": "A timeless neutral vase that complements flowers, shelves and table settings.",
                "price": "1299.00",
                "original_price": "1799.00",
                "stock": 25,
                "badge": "",
                "featured": False,
                "image_url": "https://images.unsplash.com/photo-1618220179428-22790b461013?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Fashion",
                "name": "Peter England Formal Shirt",
                "slug": "peter-england-formal-shirt",
                "short_description": "Classic formal shirt designed for office and occasion wear.",
                "description": "A smart formal shirt with a comfortable fit and clean professional finish.",
                "price": "699.00",
                "original_price": "899.00",
                "stock": 50,
                "badge": "Formal Edit",
                "featured": True,
                "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Home",
                "name": "Dot & Key Skincare Combo",
                "slug": "dot-and-key-skincare-combo",
                "short_description": "A simple skincare combo for cleansing, hydration and daily care.",
                "description": "A customer-friendly skincare selection for a fresh and hydrated daily routine.",
                "price": "749.00",
                "original_price": "999.00",
                "stock": 42,
                "badge": "Beauty Pick",
                "featured": False,
                "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?auto=format&fit=crop&w=900&q=80",
            },

            {
                "category": "Fashion",
                "name": "Levi's 511 Slim Fit Jeans",
                "slug": "levis-511-slim-fit-jeans",
                "short_description": "Classic slim-fit denim for everyday casual styling.",
                "description": "Comfortable stretch denim with a modern slim fit suitable for college, travel and casual outings.",
                "price": 2499,
                "original_price": 3299,
                "stock": 18,
                "featured": True,
                "badge": "Best Seller",
                "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Fashion",
                "name": "Nike Sportswear Hoodie",
                "slug": "nike-sportswear-hoodie",
                "short_description": "Soft everyday hoodie with a clean athletic look.",
                "description": "A comfortable fleece hoodie designed for casual wear, travel and light outdoor activity.",
                "price": 2999,
                "original_price": 3999,
                "stock": 14,
                "featured": True,
                "badge": "Trending",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Fashion",
                "name": "Peter England Formal Trousers",
                "slug": "peter-england-formal-trousers",
                "short_description": "Smart formal trousers for office and events.",
                "description": "Clean tailored trousers with a comfortable fit for interviews, office wear and formal occasions.",
                "price": 1899,
                "original_price": 2499,
                "stock": 20,
                "featured": False,
                "badge": "Office Edit",
                "image_url": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Beauty",
                "name": "Dot & Key Watermelon Sunscreen",
                "slug": "dot-key-watermelon-sunscreen",
                "short_description": "Lightweight daily sunscreen with a fresh finish.",
                "description": "A comfortable everyday sunscreen designed for hydration and broad-spectrum protection.",
                "price": 595,
                "original_price": 695,
                "stock": 35,
                "featured": True,
                "badge": "Beauty Pick",
                "image_url": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Beauty",
                "name": "Maybelline Fit Me Foundation",
                "slug": "maybelline-fit-me-foundation",
                "short_description": "Natural matte foundation for an even everyday look.",
                "description": "A lightweight foundation with buildable coverage and a smooth natural matte finish.",
                "price": 649,
                "original_price": 799,
                "stock": 28,
                "featured": True,
                "badge": "Popular",
                "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Beauty",
                "name": "Minimalist Niacinamide Serum",
                "slug": "minimalist-niacinamide-serum",
                "short_description": "Daily face serum for balanced-looking skin.",
                "description": "A simple skincare serum designed to support an even-looking complexion and daily routine.",
                "price": 599,
                "original_price": 699,
                "stock": 32,
                "featured": False,
                "badge": "Skin Care",
                "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Electronics",
                "name": "boAt Airdopes Wireless Earbuds",
                "slug": "boat-airdopes-wireless-earbuds",
                "short_description": "Compact wireless earbuds for music and calls.",
                "description": "Portable true wireless earbuds with touch controls, clear calling and convenient charging case.",
                "price": 1499,
                "original_price": 2999,
                "stock": 24,
                "featured": True,
                "badge": "Hot Deal",
                "image_url": "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Electronics",
                "name": "Logitech Wireless Mouse",
                "slug": "logitech-wireless-mouse",
                "short_description": "Reliable wireless mouse for study and office work.",
                "description": "A compact ergonomic mouse with smooth tracking and dependable wireless connectivity.",
                "price": 899,
                "original_price": 1199,
                "stock": 30,
                "featured": False,
                "badge": "Work Essential",
                "image_url": "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Electronics",
                "name": "Samsung 10000mAh Power Bank",
                "slug": "samsung-10000mah-power-bank",
                "short_description": "Portable power backup for phones and accessories.",
                "description": "A slim high-capacity power bank suitable for travel, college and daily charging needs.",
                "price": 1899,
                "original_price": 2499,
                "stock": 16,
                "featured": True,
                "badge": "Travel Pick",
                "image_url": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Footwear",
                "name": "Adidas Runfalcon Shoes",
                "slug": "adidas-runfalcon-shoes",
                "short_description": "Comfortable running shoes for everyday movement.",
                "description": "Lightweight running shoes with breathable support and cushioned comfort for daily use.",
                "price": 2799,
                "original_price": 3999,
                "stock": 19,
                "featured": True,
                "badge": "Sports Pick",
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Footwear",
                "name": "Crocs Classic Clog",
                "slug": "crocs-classic-clog",
                "short_description": "Lightweight casual clogs for all-day comfort.",
                "description": "Easy-to-wear clogs suitable for home, travel and relaxed everyday styling.",
                "price": 2495,
                "original_price": 3495,
                "stock": 22,
                "featured": False,
                "badge": "Comfort",
                "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Home",
                "name": "Home Centre Cotton Bedsheet",
                "slug": "home-centre-cotton-bedsheet",
                "short_description": "Soft printed cotton bedsheet for a fresh bedroom look.",
                "description": "A comfortable double-bed cotton bedsheet with matching pillow covers and easy-care fabric.",
                "price": 1299,
                "original_price": 1799,
                "stock": 17,
                "featured": False,
                "badge": "Home Favourite",
                "image_url": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Home",
                "name": "Milton Insulated Water Bottle",
                "slug": "milton-insulated-water-bottle",
                "short_description": "Insulated bottle for office, gym and travel.",
                "description": "A durable reusable bottle designed to keep beverages at a comfortable temperature for longer.",
                "price": 899,
                "original_price": 1199,
                "stock": 27,
                "featured": False,
                "badge": "Daily Essential",
                "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Accessories",
                "name": "Fastrack Analog Watch",
                "slug": "fastrack-analog-watch",
                "short_description": "Modern analog watch for casual everyday wear.",
                "description": "A stylish everyday watch with a clean dial and comfortable strap for college and outings.",
                "price": 1995,
                "original_price": 2495,
                "stock": 15,
                "featured": True,
                "badge": "Style Pick",
                "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&w=900&q=80",
            },
            {
                "category": "Accessories",
                "name": "Wildcraft Everyday Backpack",
                "slug": "wildcraft-everyday-backpack",
                "short_description": "Spacious backpack for college, office and short trips.",
                "description": "A practical backpack with organized storage, padded straps and space for daily essentials.",
                "price": 1699,
                "original_price": 2299,
                "stock": 21,
                "featured": True,
                "badge": "College Pick",
                "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80",
            },
        ]

        for product_data in products:
            item = product_data.copy()
            category_name = item.pop("category")
            slug = item.pop("slug")
            category = category_objects.get(category_name)
            if category is None:
                self.stderr.write(
                    self.style.WARNING(
                        f"Skipping {item.get('name', slug)}: unknown category {category_name}."
                    )
                )
                continue

            original_price = item.get("original_price")
            item["price"] = Decimal(str(item["price"]))
            item["original_price"] = (
                Decimal(str(original_price)) if original_price is not None else None
            )
            Product.objects.update_or_create(
                slug=slug,
                defaults={"category": category, **item, "available": True},
            )

        now = timezone.now()
        Coupon.objects.update_or_create(
            code="RAJ10",
            defaults={
                "valid_from": now - timedelta(days=1),
                "valid_to": now + timedelta(days=365),
                "discount": 10,
                "active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Premium demo store and RAJ10 coupon created."))
