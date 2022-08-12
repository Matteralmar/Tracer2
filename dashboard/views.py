import csv
from django.core.mail import send_mail
from django.views import generic, View
from tickets.models import *
from administration.mixins import *
from .forms import *
from django.http import HttpResponse, Http404
from django.shortcuts import render, reverse, render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count



class DashboardChartView(LoginRequiredMixin, generic.ListView):
    template_name = "dashboard/dashboard_chart.html"
    context_object_name = "projects"


    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account, archive=False)
        elif user.role == 'project_manager':
            queryset = Project.objects.filter(project_manager__user=user, archive=False, organisation=user.member.organisation)
        else:
            proj = list(user.ticket_flow.all())
            queryset = Project.objects.filter(title__in=proj, archive=False, organisation=user.member.organisation)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(DashboardChartView, self).get_context_data(**kwargs)

        if user.is_organizer:
            project = Project.objects.filter(archive=False, organisation=user.account)
            status_id = Ticket.objects.filter(organisation=user.account, project__in=project, status_id__isnull=False).values('status_id')
            priority_id = Ticket.objects.filter(organisation=user.account, project__in=project, priority_id__isnull=False).values('priority_id')
            type_id = Ticket.objects.filter(organisation=user.account, project__in=project, type_id__isnull=False).values('type_id')
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = status_id.annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = priority_id.annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = type_id.annotate(total=Count('type_id'))
            return context
        elif user.role == 'project_manager':
            project = Project.objects.filter(project_manager__user=user, archive=False)
            status_id = Ticket.objects.filter(project__in=project, status_id__isnull=False).values('status_id')
            priority_id = Ticket.objects.filter(project__in=project, priority_id__isnull=False).values('priority_id')
            type_id = Ticket.objects.filter(project__in=project, type_id__isnull=False).values('type_id')
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = status_id.annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = priority_id.annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = type_id.annotate(total=Count('type_id'))
            return context
        elif user.role == 'developer':
            project = Project.objects.filter(archive=False, organisation=user.member.organisation)
            status_id = Ticket.objects.filter(~Q(status__test_status=True), assigned_to__user=user, project__in=project, status_id__isnull=False).values('status_id')
            priority_id = Ticket.objects.filter(~Q(status__test_status=True), assigned_to__user=user, project__in=project, priority_id__isnull=False).values('priority_id')
            type_id = Ticket.objects.filter(~Q(status__test_status=True), assigned_to__user=user, project__in=project, type_id__isnull=False).values('type_id')
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = status_id.annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = priority_id.annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = type_id.annotate(total=Count('type_id'))
            return context
        else:
            project = Project.objects.filter(archive=False, organisation=user.member.organisation)
            status_id = Ticket.objects.filter(author=user, project__in=project, status_id__isnull=False).values('status_id')
            priority_id = Ticket.objects.filter(author=user, project__in=project, priority_id__isnull=False).values('priority_id')
            type_id = Ticket.objects.filter(author=user, project__in=project, type_id__isnull=False).values('type_id')
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = status_id.annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = priority_id.values('priority_id').annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = type_id.values('type_id').annotate(total=Count('type_id'))
            return context

class ProjectUpdateView(ManagerOrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/project_update.html"
    form_class = ProjectModelForm
    context_object_name = "project"


    def get_form_kwargs(self, **kwargs):
        kwargs = super(ProjectUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account, archive=False)
        else:
            queryset = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, archive=False)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        project = Project.objects.get(pk=self.kwargs["pk"])
        if self.request.user.is_organizer:
            titl = form.cleaned_data['title']
            project_manager = form.cleaned_data['project_manager']
            color_data.save()
            if (project_manager and project.project_manager is not None) and (project_manager == project.project_manager):
                Notification.objects.create(
                    title=f'Project update',
                    text=f'Your "{titl}" project was updated by {self.request.user.username}',
                    recipient=project.project_manager.user
                )

            if (project_manager and project.project_manager is not None) and (project_manager != project.project_manager):
                Notification.objects.create(
                    title=f'New project',
                    text=f'"{titl}" project was assigned to you by {self.request.user.username}',
                    recipient=project_manager.user
                )
                Notification.objects.create(
                    title=f'Unassigned project',
                    text=f'"{project.title}" project was unassigned from you by {self.request.user.username}',
                    recipient=project.project_manager.user
                )

            if project.project_manager is None and project_manager is not None:
                Notification.objects.create(
                    title=f'New project',
                    text=f'"{titl}" project was assigned to you by {self.request.user.username}',
                    recipient=project_manager.user
                )

            if project.project_manager is not None and project_manager is None:
                Notification.objects.create(
                    title=f'Unassigned project',
                    text=f'"{project.title}" project was unassigned from you by {self.request.user.username}',
                    recipient=project.project_manager.user
                )

            if project.title != titl:
                if project.project_manager is not None and project_manager == project.project_manager:
                    Notification.objects.create(
                        title=f'Project name change',
                        text=f'There was a name change of "{project.title}" into "{titl}" by {self.request.user.username}',
                        recipient=project.project_manager.user
                    )

        progress = form.cleaned_data['progress']
        if self.request.user.role == 'project_manager':
            color_data.save()
            user = User.objects.get(username=self.request.user.member.organisation)
            Notification.objects.create(
                title=f'Project update',
                text=f'"{project.title}" project was updated by {self.request.user.username}',
                recipient=user
            )
            if progress == 'closed' and project.progress != 'closed':
                Notification.objects.create(
                    title=f'Project closed',
                    text=f'"{project.title}" project was closed by {self.request.user.username}',
                    recipient=user
                )
                return super(ProjectUpdateView, self).form_valid(form)
            if progress != project.progress :
                Notification.objects.create(
                    title=f'Project status',
                    text=f'{self.request.user.username} changed status of "{project.title}" project',
                    recipient=user
                )
        return super(ProjectUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:dashboard-chart")


class ProjectDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/project_delete.html"

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(organisation=user.account, archive=False)
        return queryset

    def form_valid(self, form):
        project_id = self.kwargs["pk"]
        project = Project.objects.get(id=project_id)
        if project.project_manager is not None:
            Notification.objects.create(
                title=f'Project deletion',
                text=f'Project "{project.title}" that you manage was deleted by {self.request.user.username}',
                recipient=project.project_manager.user
            )
        return super(ProjectDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:dashboard-chart")

class ProjectCreateView(OrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/project_create.html"
    form_class = ProjectModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ProjectCreateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        project = form.save(commit=False)
        project.organisation = user.account
        color_code_client = self.request.POST['CI']
        project.color_code = color_code_client
        project.save()
        if project.project_manager is not None:
            Notification.objects.create(
                title=f'New project',
                text=f'You was assigned to a new "{project.title}" project by {self.request.user.username}',
                recipient=project.project_manager.user
            )
        return super(ProjectCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:dashboard-chart")

class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account, archive=False)
        elif user.role == 'project_manager':
            queryset = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, archive=False)
        else:
            proj = list(user.ticket_flow.all())
            queryset = Project.objects.filter(title__in=proj, archive=False, organisation=user.member.organisation )
        return queryset


class ProjectRequestChangeView(ManagerAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard/project_request_change.html"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        project = get_object_or_404(Project, project_manager__user=user, organisation=user.member.organisation, archive=False, id=self.kwargs["pk"])
        user = User.objects.get(username=user.member.organisation)
        Notification.objects.create(
            title=f'Request Change',
            text=f'{self.request.user.username} requested a change to "{project.title}" project. Please contact {self.request.user.username} for more details.',
            recipient=user
        )
        return redirect("dashboard:dashboard-chart")

class ProjectManagementView(ManagerAndLoginRequiredMixin, generic.ListView):
    template_name = "dashboard/project_management.html"
    context_object_name = "tickets"

    def get_queryset(self):
        user = self.request.user
        id = self.request.path.split('/')[4]
        self.request.session['project_id'] = id
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, id=id, archive=False)
        queryset = Ticket.objects.filter(project__in=project, assigned_to__isnull=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectManagementView, self).get_context_data(**kwargs)
        id = self.request.path.split('/')[4]
        tickets = Ticket.objects.filter(project=id, assigned_to__isnull=True)
        context["unassigned_tickets"] = tickets
        context["project"] = id
        return context

class AssignMemberView(ManagerAndLoginRequiredMixin, generic.FormView):
    template_name = "dashboard/assign_member.html"
    form_class = AssignMemberForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignMemberView, self).get_form_kwargs(**kwargs)
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        project = get_object_or_404(Project, id=ticket.project.id, archive=False, project_manager__user=user)
        kwargs.update({
            "request": self.request,
            "id": project.id,
        })
        return kwargs

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

    def form_valid(self, form):
        user = self.request.user
        member = form.cleaned_data["member"]
        ticket = Ticket.objects.get(id=self.kwargs["pk"])
        ticket.assigned_to = member
        ticket.save()
        Notification.objects.create(
            title=f'New ticket',
            text=f'"{ticket.title}" ticket was assigned to you by {self.request.user.username}',
            recipient=ticket.assigned_to.user
        )
        return super(AssignMemberView, self).form_valid(form)

class ManagementTicketCreateView(ManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/management_ticket_create.html"
    form_class = ManagementTicketCreateModelForm

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

    def get_form_kwargs(self, **kwargs):
        user = self.request.user
        kwargs = super(ManagementTicketCreateView, self).get_form_kwargs(**kwargs)
        project = get_object_or_404(Project, archive=False, project_manager__user=user)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        project = Project.objects.get(id=self.request.session['project_id'])
        ticket = form.save(commit=False)
        ticket.organisation = user.member.organisation
        ticket.project = project
        ticket.author = user
        ticket.save()
        assigned_to = form.cleaned_data['assigned_to']
        if assigned_to is not None:
            Notification.objects.create(
                title=f'New ticket',
                text=f'You was assigned a new "{ticket.title}" ticket by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=assigned_to.user
            )
        return super(ManagementTicketCreateView, self).form_valid(form)


class ManagementTicketUpdateView(ManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/management_ticket_update.html"
    form_class = ManagementTicketUpdateModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ManagementTicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, archive=False)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def form_valid(self, form):
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        assigned_to = form.cleaned_data['assigned_to']
        titl = form.cleaned_data['title']
        if (assigned_to and ticket.assigned_to is not None) and (assigned_to == ticket.assigned_to):
            Notification.objects.create(
                title=f'Ticket update',
                text=f'Your "{titl}" ticket details was updated by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=ticket.assigned_to.user
            )

        if (assigned_to and ticket.assigned_to is not None) and (assigned_to != ticket.assigned_to):
            Notification.objects.create(
                title=f'New ticket',
                text=f'"{titl}" ticket was assigned to you by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=assigned_to.user
            )
            Notification.objects.create(
                title=f'Unassigned ticket',
                text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=ticket.assigned_to.user
            )

        if ticket.assigned_to is None and assigned_to is not None:
            Notification.objects.create(
                title=f'New ticket',
                text=f'"{titl}" ticket was assigned to you by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=assigned_to.user
            )

        if ticket.assigned_to is not None and assigned_to is None:
            Notification.objects.create(
                title=f'Unassigned ticket',
                text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=ticket.assigned_to.user
            )

        if ticket.title != titl:
            if ticket.assigned_to is not None and assigned_to == ticket.assigned_to:
                Notification.objects.create(
                    title=f'Ticket name change',
                    text=f'There was a name change of "{ticket.title}" into "{titl}" by {self.request.user.username}({self.request.user.get_role_display()})',
                    recipient=ticket.assigned_to.user
                )
        return super(ManagementTicketUpdateView, self).form_valid(form)

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

class ManagementCategoryUpdateView(ManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/management_category_update.html"
    form_class = TicketCategoryUpdateForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ManagementCategoryUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation,archive=False)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

class ManagementTicketDeleteView(ManagerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/management_ticket_delete.html"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, archive=False)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

class ManagementTicketDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/management_ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, archive=False)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

class ManagementCommentCreateView(ManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/management_comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("dashboard:management-ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        project = get_object_or_404(Project, id=ticket.project.id, archive=False, project_manager__user=user)
        context = super(ManagementCommentCreateView, self).get_context_data(**kwargs)
        context.update({
            "ticket": ticket
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        if ticket.assigned_to is not None:
            Notification.objects.create(
                title=f'New comment',
                text=f'There is a new comment created for "{ticket.title}" ticket by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=ticket.assigned_to.user
            )
        return super(ManagementCommentCreateView, self).form_valid(form)

class ManagementCommentUpdateView(ManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/management_comment_update.html"
    form_class = CommentModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation, author=user)
        return queryset

    def get_success_url(self):
        return reverse("dashboard:management-ticket-detail",  kwargs={"pk": self.get_object().ticket.id})

class ManagementCommentDeleteView(ManagerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/management_comment_delete.html"

    def get_success_url(self):
        comment = Comment.objects.get(id=self.kwargs["pk"])
        return reverse("dashboard:management-ticket-detail", kwargs={"pk": comment.ticket.pk})

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation, author=user)
        return queryset


class ProjectTestView(TesterAndLoginRequiredMixin, generic.ListView):
    template_name = "dashboard/project_test.html"
    context_object_name = "tickets"

    def get_queryset(self):
        user = self.request.user
        id = self.request.path.split('/')[4]
        self.request.session['project_id'] = id
        proj = list(user.ticket_flow.filter(archive=False, id=id, organisation=user.member.organisation))
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        queryset = Ticket.objects.filter(tester=user.id, status_id__in=status_id, project__in=proj, project__archive=False)
        return queryset


class TestTicketUpdateView(TesterAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/test_ticket_update.html"
    form_class = TicketModelForm


    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-test", args=[id])

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TestTicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False, organisation=user.member.organisation)
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        queryset = Ticket.objects.filter(tester=user.id, status_id__in=status_id, project__in=project)
        return queryset

    def form_valid(self, form):
        status = form.cleaned_data['status']
        if status is not None and not status.test_status:
            id = self.kwargs["pk"]
            ticket = Ticket.objects.get(id=id)
            if ticket.project.project_manager is not None:
                Notification.objects.create(
                    title=f'Ticket tested',
                    text=f'"{ticket.title}" is in your "{ticket.project}" project tested by {self.request.user}',
                    recipient=ticket.project.project_manager.user
                )
        return super(TestTicketUpdateView, self).form_valid(form)


class TicketRequestChangeView(TesterAndLoginRequiredMixin, generic.TemplateView):
    template_name = "dashboard/ticket_request_change.html"
    context_object_name = "ticket"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        project = Project.objects.filter(archive=False, organisation=user.member.organisation)
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        ticket = get_object_or_404(Ticket, tester=user.id, status_id__in=status_id, project__in=project, id=self.kwargs["pk"])
        if ticket.project.project_manager is not None:
            Notification.objects.create(
                title=f'Request Change',
                text=f'{self.request.user.username}({self.request.user.get_role_display()}) requested a change to "{ticket.title}" ticket. Please contact {self.request.user.username} for more details.',
                recipient=ticket.project.project_manager.user
            )
        id = self.request.session['project_id']
        return redirect(f"/dashboard/project/test/{id}/")

class TestTicketDetailView(TesterAndLoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/test_ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False, organisation=user.member.organisation)
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        queryset = Ticket.objects.filter(tester=user.id, status_id__in=status_id, project__in=project)
        return queryset

class TestCommentCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/test_comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("dashboard:test-ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        user = self.request.user
        project = Project.objects.filter(archive=False, organisation=user.member.organisation)
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        ticket = get_object_or_404(Ticket, tester=user.id, status_id__in=status_id, project__in=project, id=self.kwargs["pk"])
        context = super(TestCommentCreateView, self).get_context_data(**kwargs)
        context.update({
            "ticket": ticket
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        if ticket.assigned_to is not None:
            Notification.objects.create(
                title=f'New comment',
                text=f'There is a new comment created for "{ticket.title}" ticket by {self.request.user.username}({self.request.user.get_role_display()})',
                recipient=ticket.assigned_to.user
            )
        return super(TestCommentCreateView, self).form_valid(form)

class TestCommentUpdateView(TesterAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/test_comment_update.html"
    form_class = CommentModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation, author=user)
        return queryset

    def get_success_url(self):
        return reverse("dashboard:test-ticket-detail",  kwargs={"pk": self.get_object().ticket.id})

class TestCommentDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/test_comment_delete.html"

    def get_success_url(self):
        comment = Comment.objects.get(id=self.kwargs["pk"])
        return reverse("dashboard:test-ticket-detail", kwargs={"pk": comment.ticket.pk})

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation, author=user)
        return queryset

def project_tickets_csv(request, pk):
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    if user.is_organizer or user.role == 'project_manager':
        response = HttpResponse(content_type='text/csv')
        if user.is_organizer:
            project = get_object_or_404(Project, organisation=user.account, id=pk)
        else:
            project = get_object_or_404(Project, organisation=user.member.organisation, project_manager__user=user, archive=False, id=pk)
        response['Content-Disposition'] = f'attachment; filename={project}.csv'
        writer = csv.writer(response)
        tickets = Ticket.objects.filter(project=project)
        writer.writerow(['Ticket Title', 'Assigned To', 'Status', 'Priority', 'Type', 'Created Date', 'Deadline', 'Author', 'Tester'])
        for ticket in tickets:
            writer.writerow([ticket.title, ticket.assigned_to, ticket.status, ticket.priority, ticket.type, ticket.created_date, ticket.deadline, ticket.author, ticket.tester])
        return response
    return redirect('/dashboard/')



def project_archive(request, pk):
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    if user.is_organizer:
        project = Project.objects.get(id=pk, archive=False)
        project.archive = True
        project.save()
        if project.project_manager is not None:
            Notification.objects.create(
                title=f'Project archived',
                text=f'Project "{project.title}" that you manage is now archived',
                recipient=project.project_manager.user
            )
    return redirect('/dashboard/')