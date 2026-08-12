from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum, F, DecimalField
from .models import Sale, Expense, ShopSettings

MONEY = DecimalField(max_digits=14, decimal_places=2)


def zero():
    return Decimal("0.00")


def sales_totals(qs):
    """Return revenue, cost, profit, item count for a Sale queryset."""
    agg = qs.aggregate(
        revenue=Sum(F('selling_price') * F('quantity'), output_field=MONEY),
        cost=Sum(F('purchase_price') * F('quantity'), output_field=MONEY),
        items=Sum('quantity'),
    )
    revenue = agg['revenue'] or zero()
    cost = agg['cost'] or zero()
    return {'revenue': revenue, 'cost': cost, 'profit': revenue - cost, 'items': agg['items'] or 0}


def expense_total(qs):
    return qs.aggregate(t=Sum('amount'))['t'] or zero()


def balance_before(day):
    """Cash carried into `day` = opening + all sales before it - all expenses before it."""
    opening = ShopSettings.load().opening_balance
    sales = sales_totals(Sale.objects.filter(date__lt=day))['revenue']
    exp = expense_total(Expense.objects.filter(date__lt=day))
    return opening + sales - exp


def day_stats(day):
    """Everything needed for one day's cash calculation."""
    s = sales_totals(Sale.objects.filter(date=day))
    e = expense_total(Expense.objects.filter(date=day))
    prev = balance_before(day)
    return {
        'previous': prev,
        'sales': s,
        'expenses': e,
        'closing': prev + s['revenue'] - e,
        'sale_list': Sale.objects.filter(date=day),
        'expense_list': Expense.objects.filter(date=day),
    }


def range_stats(start, end):
    s = sales_totals(Sale.objects.filter(date__gte=start, date__lte=end))
    e = expense_total(Expense.objects.filter(date__gte=start, date__lte=end))
    return {
        'sales': s,
        'expenses': e,
        'net': s['revenue'] - e,
        'sale_qs': Sale.objects.filter(date__gte=start, date__lte=end),
        'expense_qs': Expense.objects.filter(date__gte=start, date__lte=end),
    }


def week_start(day):
    """Saturday-based week start."""
    return day - timedelta(days=(day.weekday() + 2) % 7)