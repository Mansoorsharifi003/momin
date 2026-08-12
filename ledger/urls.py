from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sales/', views.sales_list, name='sales'),
    path('sales/new/', views.sale_new, name='sale_new'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),
    path('expenses/', views.expenses_list, name='expenses'),
    path('expenses/new/', views.expense_new, name='expense_new'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('reports/', views.reports, name='reports'),
    path('reports/print/', views.report_print, name='report_print'),
    path('search/', views.search, name='search'),
    path('settings/', views.settings_view, name='settings'),
    path('tools/', views.tools, name='tools'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('backup/json/', views.backup_json, name='backup_json'),
    path('restore/json/', views.restore_json, name='restore_json'),
    path('tools/reset-data/', views.reset_data, name='reset_data'),
]