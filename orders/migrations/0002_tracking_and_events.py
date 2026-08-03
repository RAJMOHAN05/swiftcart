# Generated for SwiftCart Phase 2
from django.db import migrations, models
import django.db.models.deletion


def populate_tracking(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.filter(tracking_number=""):
        order.tracking_number = f"SWCLEGACY{order.id:08d}"
        order.save(update_fields=["tracking_number"])


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="estimated_delivery",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="tracking_number",
            field=models.CharField(blank=True, editable=False, max_length=24),
        ),
        migrations.AddField(
            model_name="order",
            name="transaction_reference",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="order",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(populate_tracking, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="tracking_number",
            field=models.CharField(blank=True, editable=False, max_length=24, unique=True),
        ),
        migrations.CreateModel(
            name="OrderStatusEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("placed", "Order Placed"), ("confirmed", "Confirmed"), ("packed", "Packed"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], max_length=20)),
                ("note", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_events", to="orders.order")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
