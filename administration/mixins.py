from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from tickets.models import Project

class ManagerOrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_organizer or request.user.role == 'project_manager'):
            return redirect("tickets:ticket-list")
        return super().dispatch(request, *args, **kwargs)

class OrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_organizer:
            return redirect("tickets:ticket-list")
        return super().dispatch(request, *args, **kwargs)

class ManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        id = self.request.session['project_id']
        project = Project.objects.get(id=id)
        project_id = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        id = int(id)
        if not request.user.is_authenticated or not request.user.role == 'project_manager'or project.archive or not id in project_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class ManagerArchiveCheckAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        id = self.request.path.split('/')[4]
        project = Project.objects.get(id=id)
        project_id = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        id = int(id)
        if not request.user.is_authenticated or not request.user.role == 'project_manager' or project.archive or not id in project_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class NotManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role == 'project_manager':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)


class OrganizerTesterAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_organizer or request.user.role == 'project_manager'):
            return redirect("tickets:ticket-list")
        return super().dispatch(request, *args, **kwargs)