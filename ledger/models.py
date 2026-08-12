from django.db import models
from decimal import Decimal


class ShopSettings(models.Model):
    """Single row (pk=1) holding shop-wide settings."""
    shop_name = models.CharField(max_length=100, default="MOMIN Jewelry")
    currency = models.CharField(max_length=8, default="؋")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = "Shop Settings"
        verbose_name_plural = "Shop Settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.shop_name


CATEGORY_CHOICES = [
    ("Tea", "Tea"),
    ("Food", "Food"),
    ("Rent / Committee", "Rent / Committee"),
    ("Salary", "Salary"),
    ("Cash Taken Home", "Cash Taken Home"),
    ("Other", "Other"),
]


class Sale(models.Model):
    product_name = models.CharField(max_length=200)
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2)
    selling_price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    @property
    def total_sale(self):
        return self.selling_price * self.quantity

    @property
    def profit(self):
        return (self.selling_price - self.purchase_price) * self.quantity

    def __str__(self):
        return self.product_name


class Expense(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Other")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title