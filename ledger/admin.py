from django.contrib import admin
from .models import Sale, Expense, ShopSettings

admin.site.register(Sale)
admin.site.register(Expense)
admin.site.register(ShopSettings)