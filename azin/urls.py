"""
URL configuration for azin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings

from storage.views import (
    AuditLogView,
    ErrorLogView,
    UserUsageReportView,
    SearchAuditLogsView,
    SearchErrorLogsView
)

urlpatterns = [
    path('admin/reports/audit-logs/', AuditLogView.as_view(), name='audit_logs'),
    path('admin/reports/error-logs/', ErrorLogView.as_view(), name='error_logs'),
    path('admin/reports/user-usage/', UserUsageReportView.as_view(), name='user_usage'),
    path('admin/reports/user-usage/<str:user_id>/', UserUsageReportView.as_view(), name='user_usage_detail'),
    path('admin/reports/search-audit-logs/', SearchAuditLogsView.as_view(), name='search_audit_logs'),
    path('admin/reports/search-error-logs/', SearchErrorLogsView.as_view(), name='search_error_logs'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('storage.urls'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)