from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from tickets.models import *

class ManagerOrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_organizer or request.user.role == 'project_manager'):
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class OrganizerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_organizer:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class NotManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role == 'project_manager':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class ManagerAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.role == 'project_manager':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class TesterAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.role == 'tester':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class TstrDevAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and (not request.user.role == 'tester' or not request.user.role == 'developer'):
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class OrgDevAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and (not request.user.role == 'developer' or not request.user.is_organizer):
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class DeveloperAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.role == 'developer':
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)

class CommentAndLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user.id
        author = Comment.objects.filter(id=self.kwargs["pk"]).values_list('author', flat=True)
        if not request.user.is_authenticated or request.user.role == 'project_manager' or not user in author:
            return redirect("dashboard:dashboard-chart")
        return super().dispatch(request, *args, **kwargs)


