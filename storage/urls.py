from django.urls import path
from storage import views

urlpatterns = [
    path('', views.FileListView.as_view(), name='list_files'),
    path('upload/', views.FileUploadView.as_view(), name='upload_file'),
    path('delete/', views.FileDeleteView.as_view(), name='delete_file'),
    path('download/', views.FileDownloadView.as_view(), name='download_file'),
    path('search/', views.FileSearchView.as_view(), name='search_file'),
    path('create-folder/', views.FolderCreateView.as_view(), name='create_folder'),
    path('delete-folder/', views.FolderDeleteView.as_view(), name='delete_folder'),
    path('reports/audit-logs/', views.AuditLogView.as_view(), name='audit_logs'),
    path('reports/error-logs/', views.ErrorLogView.as_view(), name='error_logs'),
    path('reports/user-usage/', views.UserUsageReportView.as_view(), name='user_usage'),
    path('reports/user-usage/<str:user_id>/', views.UserUsageReportView.as_view(), name='user_usage_detail'),
]
