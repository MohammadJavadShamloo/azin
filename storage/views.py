import os

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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
        current_folder = request.GET.get('current_folder', '')
        bucket_name = request.user.username

        files_and_folders = storage_facade.read_object(bucket_name, current_folder)

        context = {
            'files_and_folders': files_and_folders,
            'current_folder': current_folder
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

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        try:
            logs = report_facade.get_audit_logs(size=100)
            return render(request, self.template_name, {'logs': logs})
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving audit logs: {str(e)}")


class ErrorLogView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'reports/error_logs.html'

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        try:
            logs = report_facade.get_error_logs(size=100)
            return render(request, self.template_name, {'logs': logs})
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving error logs: {str(e)}")


class UserUsageReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'reports/user_usage.html'

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        try:
            user_id = kwargs.get('user_id', None)
            if user_id:
                usage = report_facade.get_user_usage(user_id)
                return render(request, self.template_name, {'usage': usage, 'user_id': user_id})
            else:
                all_users_usage = report_facade.get_all_users_usage()
                return render(request, self.template_name, {'all_users_usage': all_users_usage})
        except Exception as e:
            return HttpResponseBadRequest(f"Error retrieving user usage: {str(e)}")


class SearchAuditLogsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'reports/audit_logs.html'

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', None)
        if search_term:
            try:
                logs = report_facade.search_audit_logs(search_term=search_term, size=100)
                return render(request, self.template_name, {'logs': logs, 'search_term': search_term})
            except Exception as e:
                return HttpResponseBadRequest(f"Error searching audit logs: {str(e)}")
        else:
            return HttpResponseBadRequest("Please provide a search term.")


class SearchErrorLogsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'reports/error_logs.html'

    def has_permission(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', None)
        if search_term:
            try:
                logs = report_facade.search_error_logs(search_term=search_term, size=100)
                return render(request, self.template_name, {'logs': logs, 'search_term': search_term})
            except Exception as e:
                return HttpResponseBadRequest(f"Error searching error logs: {str(e)}")
        else:
            return HttpResponseBadRequest("Please provide a search term.")
