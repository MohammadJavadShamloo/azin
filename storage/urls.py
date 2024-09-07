from django.urls import path
from storage import views

urlpatterns = [
    path('', views.FileListView.as_view(), name='list_files'),
    path('upload/', views.FileUploadView.as_view(), name='upload_file'),
    path('delete/', views.FileDeleteView.as_view(), name='delete_file'),
    path('download/', views.FileDownloadView.as_view(), name='download_file'),
    path('create-folder/', views.FolderCreateView.as_view(), name='create_folder'),
    path('delete-folder/', views.FolderDeleteView.as_view(), name='delete_folder'),
]
