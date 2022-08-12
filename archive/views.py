from django.shortcuts import render
from django.views import generic
from tickets.models import *
from administration.mixins import *


class ProjectArchiveListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "archive/archive_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(organisation=user.account, archive=True)
        return queryset

class ProjectArchiveDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "archive/archive_project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(organisation=user.account, archive=True)
        return queryset


def undo_archive(request, pk):
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    if user.is_organizer:
        project = Project.objects.get(id=pk, archive=True, organisation=user.account)
        project.archive = False
        project.save()
    return redirect('/dashboard/')