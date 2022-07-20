from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from tickets.models import *

class ManagerOrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_organizer or request.user.role == 'project_manager'):
            return redirect("tickets:ticket-list")
        return super().dispatch(request, *args, **kwargs)

class OrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_organizer:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class ManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            id = self.request.session['project_id']
            project = Project.objects.get(id=id)
            project_id = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        except:
            return redirect("dashboard:dashboard-chart")
        if not request.user.is_authenticated or not request.user.role == 'project_manager'or project.archive or not int(id) in project_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class ManagerArchiveCheckAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            id = self.request.path.split('/')[4]
            project = Project.objects.get(id=id)
            project_id = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        except:
            return redirect("dashboard:dashboard-chart")
        if not request.user.is_authenticated or not request.user.role == 'project_manager' or project.archive or not int(id) in project_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class TesterArchiveCheckAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            id = self.request.path.split('/')[4]
            project = Project.objects.get(id=id)
            project_id = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation).values_list('id', flat=True)
        except:
            return redirect("dashboard:dashboard-chart")
        if not request.user.is_authenticated or not request.user.role == 'tester' or project.archive or not int(id) in project_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class TesterAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            pj_id = self.request.session['project_id']
            project = Project.objects.get(id=pj_id)
            project_id = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation).values_list('id', flat=True)
            id = self.request.path.split('/')[4]
            status_id = Status.objects.filter(test_status=True, organisation=user.member.organisation).values_list('id', flat=True)
            ticket_status_id = Ticket.objects.filter(id=id, organisation=user.member.organisation).values_list('status_id', flat=True)[0]
        except:
            return redirect("dashboard:dashboard-chart")
        if not request.user.is_authenticated or not request.user.role == 'tester'or project.archive or not int(pj_id) in project_id or not ticket_status_id in status_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class TesterCommentAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            pj_id = self.request.session['project_id']
            project = Project.objects.get(id=pj_id)
            project_id = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation).values_list('id', flat=True)
            id = self.get_object().ticket.id
            status_id = Status.objects.filter(test_status=True, organisation=user.member.organisation).values_list('id', flat=True)
            ticket_status_id = Ticket.objects.filter(id=id, organisation=user.member.organisation).values_list('status_id', flat=True)[0]
        except:
            return redirect("dashboard:dashboard-chart")
        if not request.user.is_authenticated or not request.user.role == 'tester'or project.archive or not int(pj_id) in project_id or not ticket_status_id in status_id:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class NotManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role == 'project_manager':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)
