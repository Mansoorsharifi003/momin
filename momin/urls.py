from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from ledger import views as ledger_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='ledger/login.html'),
         name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('sw.js', ledger_views.service_worker, name='service_worker'),
    path('', include('ledger.urls')),
]