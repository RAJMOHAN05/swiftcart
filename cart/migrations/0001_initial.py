# Generated for SwiftCart Phase 1
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=50, unique=True)),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField()),
                ("discount", models.PositiveSmallIntegerField(help_text="Percentage discount", validators=[MinValueValidator(1), MaxValueValidator(90)])),
                ("active", models.BooleanField(default=True)),
            ],
        ),
    ]
