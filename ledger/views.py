import csv
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum, F, DecimalField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from . import services
from .forms import SaleForm, ExpenseForm, SettingsForm
from .models import Sale, Expense, ShopSettings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

def superuser_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='dashboard'          # staff get sent to Dashboard
    )(view_func)


def _parse_date(value, default):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return default


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    today = date.today()
    ledger_date = _parse_date(request.GET.get('date'), today)

    ds = services.day_stats(today)
    ledger = services.day_stats(ledger_date)

    spark = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = services.sales_totals(Sale.objects.filter(date=d))['revenue']
        spark.append({'date': d, 'sales': rev})
    max_spark = max([s['sales'] for s in spark] + [Decimal('1')])
    for s in spark:
        s['pct'] = float(s['sales'] / max_spark * 100)

    recent = []
    for s in Sale.objects.order_by('-created_at')[:10]:
        recent.append({'type': 'sale', 'label': s.product_name, 'amount': s.total_sale, 'date': s.date, 'ts': s.created_at})
    for e in Expense.objects.order_by('-created_at')[:10]:
        recent.append({'type': 'expense', 'label': e.title, 'amount': e.amount, 'date': e.date, 'ts': e.created_at})
    recent.sort(key=lambda x: x['ts'], reverse=True)

    return render(request, 'ledger/dashboard.html', {
        'settings_obj': ShopSettings.load(),
        'today': today,
        'ds': ds,
        'ledger': ledger,
        'ledger_date': ledger_date,
        'spark': spark,
        'recent': recent[:6],
    })


# ---------- Sales ----------
@login_required
def sales_list(request):
    return render(request, 'ledger/sales.html', {
        'sales': Sale.objects.all(),
        'today_stats': services.day_stats(date.today()),
        'settings_obj': ShopSettings.load(),
    })

@login_required
def sale_new(request):
    form = SaleForm(request.POST or None, initial={'date': date.today()})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sale recorded.')
        return redirect('sales')

    product_names = (Sale.objects
                     .values_list('product_name', flat=True)
                     .distinct()
                     .order_by('product_name'))

    context = {
        'form': form,
        'title': 'Record Sale',
        'product_names': product_names,
    }
    return render(request, 'ledger/sale_form.html', context)

@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    form = SaleForm(request.POST or None, instance=sale)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sale updated.')
        return redirect('sales')

    product_names = (Sale.objects
                     .values_list('product_name', flat=True)
                     .distinct()
                     .order_by('product_name'))

    context = {
        'form': form,
        'title': 'Edit Sale',
        'product_names': product_names,
    }
    return render(request, 'ledger/sale_form.html', context)

@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale deleted.')
        return redirect('sales')
    return render(request, 'ledger/confirm_delete.html', {'object': sale, 'kind': 'sale'})


# ---------- Expenses ----------
@login_required
def expenses_list(request):
    return render(request, 'ledger/expenses.html', {
        'expenses': Expense.objects.all(),
        'today_stats': services.day_stats(date.today()),
        'settings_obj': ShopSettings.load(),
    })

@login_required
def expense_new(request):
    form = ExpenseForm(request.POST or None, initial={'date': date.today()})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Expense saved.')
        return redirect('expenses')
    return render(request, 'ledger/expense_form.html', {'form': form, 'title': 'Add Expense'})

@login_required
def expense_edit(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=exp)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Expense updated.')
        return redirect('expenses')
    return render(request, 'ledger/expense_form.html', {'form': form, 'title': 'Edit Expense'})

@login_required
def expense_delete(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        exp.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expenses')
    return render(request, 'ledger/confirm_delete.html', {'object': exp, 'kind': 'expense'})


# ---------- Reports ----------

def _report_range(request):
    today = date.today()
    period = request.GET.get('period', 'today')
    if period == 'today':
        start = end = today
    elif period == 'yesterday':
        start = end = today - timedelta(days=1)
    elif period == 'week':
        start, end = services.week_start(today), today
    elif period == 'month':
        start, end = today.replace(day=1), today
    elif period == 'year':
        start, end = today.replace(month=1, day=1), today
    elif period == 'custom':
        start = _parse_date(request.GET.get('from'), today)
        end = _parse_date(request.GET.get('to'), today)
    else:
        start = end = today
    if start > end:
        start, end = end, start
    return period, start, end


def _report_context(request):
    period, start, end = _report_range(request)
    stats = services.range_stats(start, end)
    top_products = (Sale.objects.filter(date__gte=start, date__lte=end)
        .values('product_name')
        .annotate(qty=Sum('quantity'),
                  revenue=Sum(F('selling_price') * F('quantity'), output_field=DecimalField()),
                  profit=Sum((F('selling_price') - F('purchase_price')) * F('quantity'), output_field=DecimalField()))
        .order_by('-revenue')[:5])
    cat_break = (Expense.objects.filter(date__gte=start, date__lte=end)
        .values('category').annotate(total=Sum('amount')).order_by('-total'))
    max_cat = max([c['total'] for c in cat_break] + [Decimal('1')])
    return period, start, end, stats, top_products, cat_break, max_cat


def _report_series(start, end):
    raw = []
    days = (end - start).days + 1
    if days <= 31:
        for i in range(days):
            d = start + timedelta(days=i)
            s = services.sales_totals(Sale.objects.filter(date=d))['revenue']
            e = services.expense_total(Expense.objects.filter(date=d))
            raw.append({'label': d.strftime('%d'), 'full': d.strftime('%a %d %b'), 's': s, 'e': e})
    else:
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            s = services.sales_totals(Sale.objects.filter(date__year=y, date__month=m))['revenue']
            e = services.expense_total(Expense.objects.filter(date__year=y, date__month=m))
            raw.append({'label': date(y, m, 1).strftime('%b'), 'full': date(y, m, 1).strftime('%b %Y'), 's': s, 'e': e})
            m += 1
            if m > 12: m = 1; y += 1
    maxv = max([max(r['s'], r['e']) for r in raw] + [Decimal('1')])
    for r in raw:
        r['ps'] = round(float(r['s'] / maxv) * 100, 1)
        r['pe'] = round(float(r['e'] / maxv) * 100, 1)
    return raw

@login_required
def reports(request):
    period, start, end, stats, top_products, cat_break, max_cat = _report_context(request)
    return render(request, 'ledger/reports.html', {
        'period': period, 'start': start, 'end': end, 'stats': stats,
        'top_products': top_products, 'cat_break': cat_break, 'max_cat': max_cat,
        'series': _report_series(start, end),
        'settings_obj': ShopSettings.load(),
    })

@login_required
def report_print(request):
    period, start, end, stats, top_products, cat_break, max_cat = _report_context(request)
    return render(request, 'ledger/report_print.html', {
        'period': period, 'start': start, 'end': end, 'stats': stats,
        'settings_obj': ShopSettings.load(),
    })


# ---------- Search ----------
@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    sale_results = expense_results = []
    if q:
        sale_results = Sale.objects.filter(
            Q(product_name__icontains=q) | Q(notes__icontains=q) | Q(date__icontains=q))
        expense_results = Expense.objects.filter(
            Q(title__icontains=q) | Q(category__icontains=q) | Q(notes__icontains=q) | Q(date__icontains=q))
    return render(request, 'ledger/search.html', {
        'q': q, 'sale_results': sale_results, 'expense_results': expense_results,
        'settings_obj': ShopSettings.load(),
    })


# ---------- Settings & Tools ----------
@login_required
@superuser_required
def settings_view(request):
    obj = ShopSettings.load()
    form = SettingsForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Settings saved.')
        return redirect('settings')
    return render(request, 'ledger/settings.html', {'form': form, 'settings_obj': obj})

@login_required
@superuser_required
def tools(request):
    return render(request, 'ledger/tools.html', {
        'settings_obj': ShopSettings.load(),
        'sales_count': Sale.objects.count(),
        'expenses_count': Expense.objects.count(),
    })


# ---------- Export / Backup ----------
@login_required
def export_csv(request):
    period, start, end, stats, *_ = _report_context(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="momin-{start}_{end}.csv"'
    response.write('\ufeff')  # BOM so Excel reads it correctly
    w = csv.writer(response)

    w.writerow([f'MOMIN JEWELRY — REPORT {start} to {end}'])
    w.writerow(['Generated', date.today().isoformat()])
    w.writerow([])
    w.writerow(['SALES'])
    w.writerow(['Date', 'Product', 'Qty', 'Purchase Price', 'Selling Price', 'Total Sale', 'Profit', 'Notes'])
    for r in stats['sale_qs']:
        w.writerow([r.date, r.product_name, r.quantity, r.purchase_price, r.selling_price, r.total_sale, r.profit, r.notes])
    w.writerow([])
    w.writerow(['EXPENSES'])
    w.writerow(['Date', 'Title', 'Category', 'Amount', 'Notes'])
    for r in stats['expense_qs']:
        w.writerow([r.date, r.title, r.category, r.amount, r.notes])
    w.writerow([])
    w.writerow(['SUMMARY'])
    w.writerow(['Total Sales', stats['sales']['revenue']])
    w.writerow(['Gross Profit', stats['sales']['profit']])
    w.writerow(['Total Expenses', stats['expenses']])
    w.writerow(['Net Balance', stats['net']])
    return response

@login_required
@superuser_required
def backup_json(request):
    data = {
        'app': 'MOMIN Jewelry',
        'version': 1,
        'exported_at': timezone.now().isoformat(),
        'settings': {
            'shop_name': ShopSettings.load().shop_name,
            'currency': ShopSettings.load().currency,
            'opening_balance': str(ShopSettings.load().opening_balance),
        },
        'sales': list(Sale.objects.values()),
        'expenses': list(Expense.objects.values()),
    }
    response = HttpResponse(json.dumps(data, default=str, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="momin-backup.json"'
    return response

@login_required
@superuser_required
def restore_json(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            data = json.load(request.FILES['file'])
            Sale.objects.all().delete()
            Expense.objects.all().delete()
            for s in data.get('sales', []):
                Sale.objects.create(
                    product_name=s['product_name'],
                    purchase_price=s['purchase_price'],
                    selling_price=s['selling_price'],
                    quantity=s['quantity'],
                    date=s['date'],
                    notes=s.get('notes', ''),
                )
            for e in data.get('expenses', []):
                Expense.objects.create(
                    title=e['title'],
                    category=e['category'],
                    amount=e['amount'],
                    date=e['date'],
                    notes=e.get('notes', ''),
                )
            if data.get('settings'):
                obj = ShopSettings.load()
                obj.opening_balance = Decimal(str(data['settings'].get('opening_balance', obj.opening_balance)))
                obj.currency = data['settings'].get('currency', obj.currency)
                obj.save()
            messages.success(request, 'Backup restored successfully.')
        except Exception as ex:
            messages.error(request, f'Invalid backup file: {ex}')
        return redirect('tools')
    return redirect('tools')


@never_cache
def service_worker(request):
    js = """
    const CACHE_NAME = 'momin-static-v1';

    self.addEventListener('install', e => { self.skipWaiting(); });

    self.addEventListener('activate', e => {
      e.waitUntil(
        caches.keys().then(keys =>
          Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
      );
      self.clients.claim();
    });

    // Cache static assets for speed; always hit network for pages & data (safe for a ledger)
    self.addEventListener('fetch', e => {
      const url = new URL(e.request.url);
      if (url.pathname.startsWith('/static/')) {
        e.respondWith(
          caches.match(e.request).then(cached => {
            return cached || fetch(e.request).then(response => {
              const copy = response.clone();
              caches.open(CACHE_NAME).then(cache => cache.put(e.request, copy));
              return response;
            });
          })
        );
      }
    });
    """
    return HttpResponse(js, content_type='application/javascript')

@login_required
@superuser_required
def reset_data(request):
    if request.method == 'POST':
        Sale.objects.all().delete()
        Expense.objects.all().delete()
        s = ShopSettings.load()
        s.opening_balance = 0
        s.save()
        messages.success(request, 'All sales & expenses deleted. Balances reset to zero. Users were kept.')
    return redirect('tools')