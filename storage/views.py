import os

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import DeleteView, View

from storage.report_utils import ReportFacade
from storage.storage_utils import StorageFacade

storage_facade = StorageFacade()
report_facade = ReportFacade()


class FileListView(LoginRequiredMixin, View):
    template_name = 'storage/list_files.html'

    def get(self, request, *args, **kwargs):
        current_folder = request.GET.get('current_folder', '').lstrip('/').rstrip('/')
        bucket_name = request.user.username

        files_and_folders = storage_facade.read_object(bucket_name, current_folder)

        if current_folder.count('/') < 1:
            parent_folder = ''
        else:
            parent_folder = '/'.join(current_folder.split('/')[:-1])

        context = {
            'files_and_folders': files_and_folders,
            'current_folder': current_folder,
            'parent_folder': parent_folder
        }

        return render(request, self.template_name, context)


class FileUploadView(LoginRequiredMixin, View):
    template_name = 'storage/upload_file.html'

    def post(self, request, *args, **kwargs):
        file = request.FILES['file']
        uploading_folder = request.GET.get('current_folder', '')
        file_path = os.path.join(uploading_folder, file.name)

        file_content = file.read()

        bucket_name = request.user.username
        storage_facade.create_object(bucket_name, file_path, file_content)

        return redirect(f"{reverse('list_files')}?current_folder={uploading_folder}")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'current_folder': request.GET.get('current_folder', '')})


class FileDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'storage/delete_file.html'

    def get(self, request, *args, **kwargs):
        context = {
            'current_folder': request.GET.get('current_folder', ''),
            'file': request.GET.get('file')
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        current_folder = request.GET.get('current_folder', '')
        deleting_file = request.POST.get('file')

        bucket_name = request.user.username
        storage_facade.delete_object(bucket_name, os.path.join(current_folder, deleting_file))

        return redirect(f"{reverse('list_files')}?current_folder={current_folder}")


class FileDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            current_folder = request.GET.get('current_folder', '')
            file = request.GET.get('file')
            bucket_name = request.user.username
            file_path = os.path.join(current_folder, file)
            download_info = storage_facade.read_object(bucket_name, file_path)
            return redirect(download_info.get("download_link"))
        except Exception as e:
            return HttpResponseNotFound(f"File not found: {str(e)}")


class FileSearchView(LoginRequiredMixin, View):
    template_name = 'storage/file_search.html'
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        page_number = int(request.GET.get('page', 1))

        try:
            search_results = storage_facade.search_object(self.request.user.username,
                                                          search_term) if search_term else []

            paginator = Paginator(search_results, self.paginate_by)
            page_obj = paginator.get_page(page_number)

            return render(request, self.template_name, {
                'files': page_obj.object_list,
                'page_obj': page_obj,
                'search_term': search_term,
                'total_files': len(search_results),
            })
        except Exception as e:
            return HttpResponseBadRequest(f"Error searching files: {str(e)}")


class FolderCreateView(LoginRequiredMixin, View):
    template_name = 'storage/create_folder.html'

    def post(self, request, *args, **kwargs):
        new_folder_name = request.POST.get('folder')
        current_folder = request.GET.get('current_folder', '')

        if new_folder_name:
            full_path = os.path.join(current_folder, new_folder_name)
            bucket_name = request.user.username
            storage_facade.create_folder(bucket_name, full_path)

            return redirect(f"{reverse('list_files')}?current_folder={full_path}")

        return redirect('list_files')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'current_folder': request.GET.get('current_folder', '')})


class FolderDeleteView(LoginRequiredMixin, View):
    template_name = 'storage/delete_folder.html'

    def get(self, request, *args, **kwargs):
        context = {
            'current_folder': request.GET.get('current_folder', ''),
            'folder': request.GET.get('folder', '')
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        current_folder = request.GET.get('current_folder', '')
        deleting_folder_name = request.POST.get('folder')

        full_path = os.path.join(current_folder, deleting_folder_name)
        bucket_name = request.user.username

        storage_facade.delete_object(bucket_name, full_path)

        return redirect(f"{reverse('list_files')}?current_folder={current_folder}")


class AuditLogView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'storage/audit_logs.html'
    paginate_by = 20

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        try:
            page_number = int(request.GET.get('page', 1))

            if not search_term:
                logs = report_facade.get_audit_logs()
            else:
                logs = report_facade.search_audit_logs(search_term=search_term)

            paginator = Paginator(logs, self.paginate_by)
            page_obj = paginator.get_page(page_number)

            return render(request, self.template_name, {
                'logs': page_obj.object_list,
                'page_obj': page_obj,
                'total_logs': len(logs),
                'search_term': search_term
            })
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving audit logs: {str(e)}")


class ErrorLogView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'storage/error_logs.html'
    paginate_by = 20

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        try:
            page_number = int(request.GET.get('page', 1))

            if not search_term:
                logs = report_facade.get_error_logs()
            else:
                logs = report_facade.search_error_logs(search_term=search_term)

            paginator = Paginator(logs, self.paginate_by)
            page_obj = paginator.get_page(page_number)

            return render(request, self.template_name, {
                'logs': page_obj.object_list,
                'page_obj': page_obj,
                'total_logs': len(logs),
                'search_term': search_term
            })
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving error logs: {str(e)}")


class UserUsageReportView(LoginRequiredMixin, View):
    template_name = 'storage/user_usage.html'

    def get(self, request, *args, **kwargs):
        try:
            usage = report_facade.get_user_usage(self.request.user.username)
            return render(request, self.template_name, {'usage': usage, 'user_id': self.request.user.username})
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving user usage: {str(e)}")
