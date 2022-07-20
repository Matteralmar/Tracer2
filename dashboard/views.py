import csv
from django.views import View
from django.core.mail import send_mail
from django.views import generic
from tickets.models import *
from administration.mixins import *
from .forms import *
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, reverse, render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardChartView(LoginRequiredMixin, generic.ListView):
    template_name = "dashboard/dashboard_chart.html"
    context_object_name = "projects"


    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account)
        elif user.role == 'project_manager':
            queryset = Project.objects.filter(organisation=user.member.organisation)
            queryset = queryset.filter(project_manager__user=user)
        else:
            queryset = Project.objects.filter(title=user.ticket_flow)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(DashboardChartView, self).get_context_data(**kwargs)

        if user.is_organizer:
            project = Project.objects.filter(archive=False)
            status_id = Ticket.objects.filter(organisation=user.account, project__in=project).values_list('status_id', flat=True)
            priority_id = Ticket.objects.filter(organisation=user.account, project__in=project).values_list('priority_id', flat=True)
            type_id = Ticket.objects.filter(organisation=user.account, project__in=project).values_list('type_id', flat=True)
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = Ticket.objects.filter(organisation=user.account, status_id__isnull=False, project__in=project).values('status_id').annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = Ticket.objects.filter(organisation=user.account, priority_id__isnull=False, project__in=project).values('priority_id').annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = Ticket.objects.filter(organisation=user.account, type_id__isnull=False, project__in=project).values('type_id').annotate(total=Count('type_id'))
            return context
        elif user.role == 'project_manager':
            project = Project.objects.filter(project_manager__user=user, archive=False).values_list('id', flat=True)
            status_id = Ticket.objects.filter(project__in=project).values_list('status_id', flat=True)
            priority_id = Ticket.objects.filter(project__in=project).values_list('priority_id', flat=True)
            type_id = Ticket.objects.filter(project__in=project).values_list('type_id', flat=True)
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = Ticket.objects.filter(project__in=project, status_id__isnull=False).values('status_id').annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = Ticket.objects.filter(project__in=project, priority_id__isnull=False).values('priority_id').annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = Ticket.objects.filter(project__in=project, type_id__isnull=False).values('type_id').annotate(total=Count('type_id'))
            return context
        elif user.role == 'developer':
            project = Project.objects.filter(archive=False)
            status_id = Ticket.objects.filter(assigned_to__user=user, project__in=project).values_list('status_id', flat=True)
            priority_id = Ticket.objects.filter(assigned_to__user=user, project__in=project).values_list('priority_id',flat=True)
            type_id = Ticket.objects.filter(assigned_to__user=user, project__in=project).values_list('type_id', flat=True)
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = Ticket.objects.filter(assigned_to__user=user, status_id__isnull=False, project__in=project).values('status_id').annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = Ticket.objects.filter(assigned_to__user=user, priority_id__isnull=False, project__in=project).values('priority_id').annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = Ticket.objects.filter(assigned_to__user=user, type_id__isnull=False, project__in=project).values('type_id').annotate(total=Count('type_id'))
            return context
        else:
            project = Project.objects.filter(archive=False)
            status_id = Ticket.objects.filter(author=user, project__in=project).values_list('status_id', flat=True)
            priority_id = Ticket.objects.filter(author=user, project__in=project).values_list('priority_id', flat=True)
            type_id = Ticket.objects.filter(author=user, project__in=project).values_list('type_id', flat=True)
            context["statuses"] = Status.objects.filter(pk__in=status_id)
            context["count_statuses"] = Ticket.objects.filter(author=user, status_id__isnull=False, project__in=project).values('status_id').annotate(total=Count('status_id'))
            context["priorities"] = Priority.objects.filter(pk__in=priority_id)
            context["count_priorities"] = Ticket.objects.filter(author=user,priority_id__isnull=False, project__in=project).values('priority_id').annotate(total=Count('priority_id'))
            context["types"] = Type.objects.filter(pk__in=type_id)
            context["count_types"] = Ticket.objects.filter(author=user, type_id__isnull=False, project__in=project).values('type_id').annotate(total=Count('type_id'))
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
            queryset = Project.objects.filter(organisation=user.account)
        else:
            queryset = Project.objects.filter(organisation=user.member.organisation)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectUpdateView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        else:
            queryset = Project.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        context.update({
            "color_code": queryset[0],
        })
        return context

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        color_data.save()
        return super(ProjectUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:project-detail", kwargs={"pk": self.kwargs["pk"]})


class ProjectDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/project_delete.html"

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(organisation=user.account)
        return queryset

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
        return super(ProjectCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:dashboard-chart")

class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Project.objects.filter(organisation=user.account)
        else:
            queryset = Project.objects.filter(organisation=user.member.organisation)
        return queryset


class ProjectManagementView(ManagerArchiveCheckAndLoginRequiredMixin, generic.ListView):
    template_name = "dashboard/project_management.html"
    context_object_name = "tickets"

    def get_queryset(self):
        user = self.request.user
        id = self.request.path.split('/')[4]
        self.request.session['project_id'] = id
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, id=id).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ProjectManagementView, self).get_context_data(**kwargs)
        id = self.request.path.split('/')[4]
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation, id=id).values_list('id', flat=True)
        self.request.session['project_id'] = id

        status_id = Ticket.objects.filter(project__in=project).values_list('status_id', flat=True)
        priority_id = Ticket.objects.filter(project__in=project).values_list('priority_id', flat=True)
        type_id = Ticket.objects.filter(project__in=project).values_list('type_id', flat=True)

        status_color = Status.objects.filter(pk__in=status_id).values_list('color_code', flat=True)
        priority_color = Priority.objects.filter(pk__in=priority_id).values_list('color_code', flat=True)
        type_color = Type.objects.filter(pk__in=type_id).values_list('color_code', flat=True)

        if len(status_color) != 0:
            context["status_color_code"] = status_color[0]
        if len(priority_color) != 0:
            context["priority_color_code"] = priority_color[0]
        if len(type_color) != 0:
            context["type_color_code"] = type_color[0]
        return context


class ManagementTicketCreateView(ManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/management_ticket_create.html"
    form_class = TicketModelForm

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ManagementTicketCreateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        id = self.request.session['project_id']
        project = Project.objects.get(id=id)
        ticket = form.save(commit=False)
        ticket.organisation = user.member.organisation
        ticket.project = project
        ticket.author = user
        ticket.save()
        return super(ManagementTicketCreateView, self).form_valid(form)


class ManagementTicketUpdateView(ManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/management_ticket_update.html"
    form_class = TicketModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ManagementTicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

class ManagementTicketDeleteView(ManagerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/management_ticket_delete.html"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-management", args=[id])

class ManagementTicketDetailView(ManagerAndLoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/management_ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

class ManagementCommentCreateView(ManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/management_comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("dashboard:management-ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super(ManagementCommentCreateView, self).get_context_data(**kwargs)
        context.update({
            "ticket": Ticket.objects.get(pk=self.kwargs["pk"])
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        return super(ManagementCommentCreateView, self).form_valid(form)

class ManagementCommentUpdateView(ManagerCommentAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/management_comment_update.html"
    form_class = CommentModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset

    def get_success_url(self):
        return reverse("dashboard:management-ticket-detail",  kwargs={"pk": self.get_object().ticket.id})

class ManagementCommentDeleteView(ManagerCommentAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/management_comment_delete.html"

    def get_success_url(self):
        comment = Comment.objects.get(id=self.kwargs["pk"])
        return reverse("dashboard:management-ticket-detail", kwargs={"pk": comment.ticket.pk})

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset


class ProjectTestView(TesterArchiveCheckAndLoginRequiredMixin, generic.ListView):
    template_name = "dashboard/project_test.html"
    context_object_name = "tickets"

    def get_queryset(self):
        user = self.request.user
        id = self.request.path.split('/')[4]
        self.request.session['project_id'] = id
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        project = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation, id=id).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project, status_id__in=status_id)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ProjectTestView, self).get_context_data(**kwargs)
        id = self.request.path.split('/')[4]
        project = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation, id=id).values_list('id', flat=True)
        self.request.session['project_id'] = id

        status_id = Ticket.objects.filter(project__in=project).values_list('status_id', flat=True)
        priority_id = Ticket.objects.filter(project__in=project).values_list('priority_id', flat=True)
        type_id = Ticket.objects.filter(project__in=project).values_list('type_id', flat=True)

        status_color = Status.objects.filter(pk__in=status_id).values_list('color_code', flat=True)
        priority_color = Priority.objects.filter(pk__in=priority_id).values_list('color_code', flat=True)
        type_color = Type.objects.filter(pk__in=type_id).values_list('color_code', flat=True)

        if len(status_color) != 0:
            context["status_color_code"] = status_color[0]
        if len(priority_color) != 0:
            context["priority_color_code"] = priority_color[0]
        if len(type_color) != 0:
            context["type_color_code"] = type_color[0]
        return context

class TestTicketUpdateView(TesterAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/test_ticket_update.html"
    form_class = TicketModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TestTicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

    def get_success_url(self):
        id = self.request.session['project_id']
        return reverse("dashboard:project-test", args=[id])


class TestTicketDetailView(TesterAndLoginRequiredMixin, generic.DetailView):
    template_name = "dashboard/test_ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(title=user.ticket_flow, organisation=user.member.organisation).values_list('id', flat=True)
        queryset = Ticket.objects.filter(project__in=project)
        return queryset

class TestCommentCreateView(TesterAndLoginRequiredMixin, generic.CreateView):
    template_name = "dashboard/test_comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("dashboard:test-ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super(TestCommentCreateView, self).get_context_data(**kwargs)
        context.update({
            "ticket": Ticket.objects.get(pk=self.kwargs["pk"])
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        return super(TestCommentCreateView, self).form_valid(form)

class TestCommentUpdateView(TesterCommentAndLoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/test_comment_update.html"
    form_class = CommentModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset

    def get_success_url(self):
        return reverse("dashboard:test-ticket-detail",  kwargs={"pk": self.get_object().ticket.id})

class TestCommentDeleteView(TesterCommentAndLoginRequiredMixin, generic.DeleteView):
    template_name = "dashboard/test_comment_delete.html"

    def get_success_url(self):
        comment = Comment.objects.get(id=self.kwargs["pk"])
        return reverse("dashboard:test-ticket-detail", kwargs={"pk": comment.ticket.pk})

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset

def project_tickets_csv(request, pk):
    user = request.user
    if user.role == 'project_manager':
        project_id = Project.objects.filter(project_manager__user=user, organisation=user.member.organisation).values_list('id', flat=True)
    if user.is_organizer or pk in project_id:
        response = HttpResponse(content_type='text/csv')
        if user.is_organizer:
            project = Project.objects.filter(organisation=user.account, id=pk).values_list('title', flat=True)[0]
        else:
            project = Project.objects.filter(organisation=user.member.organisation, id=pk).values_list('title', flat=True)[0]
        response['Content-Disposition'] = f'attachment; filename={project}.csv'
        writer = csv.writer(response)
        project = Project.objects.filter(organisation=user.account, id=pk)
        tickets = Ticket.objects.filter(project__in=project)
        writer.writerow(['Ticket Title', 'Assigned To', 'Status', 'Priority', 'Type', 'Created Date', 'Due To', 'Author'])
        for ticket in tickets:
            writer.writerow([ticket.title, ticket.assigned_to, ticket.status, ticket.priority, ticket.type, ticket.created_date, ticket.due_to, ticket.author])
        return response
    return redirect('/dashboard/')



def project_archive(request, pk):
    user = request.user
    if user.is_organizer:
        project = Project.objects.get(id=pk)
        project.archive = True
        project.save()
    return redirect('/dashboard/')