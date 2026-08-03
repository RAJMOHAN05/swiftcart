from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Percentage discount",
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
