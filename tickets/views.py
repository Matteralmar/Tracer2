from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.views import generic
from .models import *
from .forms import *
from administration.mixins import *
from django.db.models import Count, Q


#class ProjectAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
#    def get_queryset(self):
#        qs = Project.objects.all()
#        assigned_to = self.forwarded.get('assigned_to', None)
#        print(assigned_to)
#        if self.request.user.is_organizer:
#            results = User.objects.filter(id=assigned_to)
#            for usr in results:
#                proj = list(usr.ticket_flow.all())
#            qs = qs.filter(title__in=proj, archive=False)
#        if self.request.user.role == 'project_manager':
#            results = User.objects.filter(id=assigned_to)
#            for usr in results:
#                proj = list(usr.ticket_flow.all())
#            qs = qs.filter(project_manager__user=user, archive=False) & Project.objects.filter(title__in=proj, archive=False)
#        if self.request.user.role == 'tester':
#            results = User.objects.filter(id=assigned_to)
#            for usr in results:
#                proj_1 = list(usr.ticket_flow.all())
#            results = User.objects.filter(id=self.request.user.id)
#            for usr in results:
#                proj_2 = list(usr.ticket_flow.all())
#            qs = qs.filter(title__in=proj_1, archive=False) & Project.objects.filter(title__in=proj_2,archive=False)
#        if self.request.user.role == 'developer':
#            results = User.objects.filter(id=assigned_to)
#            for usr in results:
#                proj = list(usr.ticket_flow.all())
#            qs = qs.filter(title__in=proj, archive=False)
#        return qs


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()
        username = form.cleaned_data['username']
        user = User.objects.get(username=username)
        Notification.objects.create(
            title=f'Welcome to Tracer',
            text=f'Hello {username}, hope you will enjoy your work using our app!',
            recipient=user
        )
        return super(SignupView, self).form_valid(form)

    def get_success_url(self):
        return reverse("login")


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard-chart')
        return super(LandingPageView, self).dispatch(request, *args, **kwargs)

class TicketListView(NotManagerAndLoginRequiredMixin, generic.ListView):
    template_name = "tickets/tickets_list.html"
    context_object_name = "tickets"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, assigned_to__isnull=False)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, assigned_to__isnull=False)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(TicketListView, self).get_context_data(**kwargs)
        project = Project.objects.filter(organisation=user.account, archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, assigned_to__isnull=True, project__in=project)
        context.update({
            "unassigned_tickets": queryset
        })
        return context


class TicketDetailView(NotManagerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/tickets_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user)
        return queryset


class TicketCreateView(NotManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/ticket_create.html"
    form_class = TicketModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TicketCreateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("tickets:ticket-list")

    def form_valid(self, form):
        user = self.request.user
        if user.is_organizer:
            ticket = form.save(commit=False)
            ticket.organisation = user.account
            ticket.author = user
            ticket.save()
        else:
            ticket = form.save(commit=False)
            ticket.organisation = user.member.organisation
            ticket.author = user
            ticket.save()
        if user.role != 'developer':
            titl = form.cleaned_data['title']
            assigned_to = form.cleaned_data['assigned_to']
            project = form.cleaned_data['project']
            if assigned_to is not None:
                user = User.objects.get(username=assigned_to)
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'You was assigned a new "{titl}" ticket by {self.request.user.username}',
                    recipient=user
                )
            manager_id = Project.objects.filter(title=project).values_list('project_manager', flat=True)[0]
            if manager_id is not None:
                user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)[0]
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'{self.request.user.username} created "{titl}" ticket for "{project}" project',
                    recipient=user
                )
            return super(TicketCreateView, self).form_valid(form)
        else:
            titl = form.cleaned_data['title']
            project = form.cleaned_data['project']
            manager_id = Project.objects.filter(title=project).values_list('project_manager', flat=True)[0]
            if manager_id is not None:
                user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)[0]
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'{self.request.user.username} created "{titl}" ticket for "{project}" project',
                    recipient=user
                )
            return super(TicketCreateView, self).form_valid(form)



class TicketUpdateView(NotManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/ticket_update.html"
    form_class = TicketModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user)
        return queryset


    def get_success_url(self):
        return reverse("tickets:ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if user.role != 'developer':
            titl = form.cleaned_data['title']
            assigned_to = form.cleaned_data['assigned_to']
            project = form.cleaned_data['project']
            if ticket.title != titl:
                if ticket.assigned_to is not None and ticket.assigned_to == assigned_to:
                    user = User.objects.get(username=ticket.assigned_to)
                    Notification.objects.create(
                        title=f'Ticket name change',
                        text=f'There was a name change of "{ticket.title}" into "{titl}" by {self.request.user.username}',
                        recipient=user
                    )
                manager_id = Project.objects.filter(title=ticket.project).values_list('project_manager', flat=True)[0]
                if manager_id is not None:
                    user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)
                    user = User.objects.get(id=user_id[0])
                    Notification.objects.create(
                        title=f'Ticket name change',
                        text=f'There was a name change of "{ticket.title}" into "{titl}" of your "{ticket.project}" project by {self.request.user.username}',
                        recipient=user
                    )
            if (assigned_to and ticket.assigned_to is not None) and (assigned_to == ticket.assigned_to):
                user = User.objects.get(username=ticket.assigned_to)
                Notification.objects.create(
                    title=f'Ticket update',
                    text=f'Your "{titl}" ticket details was updated by {self.request.user.username}',
                    recipient=user
                )
            if (assigned_to and ticket.assigned_to is not None) and (assigned_to != ticket.assigned_to):
                user = User.objects.get(username=assigned_to)
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'"{titl}" ticket was assigned to you by {self.request.user.username}',
                    recipient=user
                )
                user = User.objects.get(username=ticket.assigned_to)
                Notification.objects.create(
                    title=f'Unassigned ticket',
                    text=f'"{titl}" ticket was unassigned from you by {self.request.user.username}',
                    recipient=user
                )
            if ticket.assigned_to is None and assigned_to is not None:
                user = User.objects.get(username=assigned_to)
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'"{titl}" ticket was assigned to you by {self.request.user.username}',
                    recipient=user
                )
            if ticket.assigned_to is not None and assigned_to is None:
                user = User.objects.get(username=ticket.assigned_to)
                Notification.objects.create(
                    title=f'Unassigned ticket',
                    text=f'"{titl}" ticket was unassigned from you by {self.request.user.username}',
                    recipient=user
                )

            if (project and ticket.project is not None) and (project == ticket.project):
                manager_id = Project.objects.filter(title=ticket.project).values_list('project_manager', flat=True)[0]
                if manager_id is not None:
                    user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)
                    user = User.objects.get(id=user_id[0])
                    Notification.objects.create(
                        title=f'Ticket update',
                        text=f'{self.request.user.username} updated "{titl}" ticket for "{project}" project',
                        recipient=user
                    )
            if (project and ticket.project is not None) and (project != ticket.project):
                manager_id = Project.objects.filter(title=project).values_list('project_manager', flat=True)[0]
                if manager_id is not None:
                    user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)
                    user = User.objects.get(id=user_id[0])
                    Notification.objects.create(
                        title=f'New ticket',
                        text=f'"{titl}" ticket was assigned to your "{project}" project by {self.request.user.username}',
                        recipient=user
                    )
                manager_id = Project.objects.filter(title=ticket.project).values_list('project_manager', flat=True)[0]
                if manager_id is not None:
                    user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)
                    user = User.objects.get(id=user_id[0])
                    Notification.objects.create(
                        title=f'Unassigned ticket',
                        text=f'"{titl}" ticket was unassigned from your "{ticket.project}" project by {self.request.user.username}',
                        recipient=user
                    )
            return super(TicketUpdateView, self).form_valid(form)
        return super(TicketUpdateView, self).form_valid(form)


class TicketDeleteView(NotManagerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/ticket_delete.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user)
        return queryset

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if user.role != 'developer':
            if ticket.assigned_to is not None:
                user = User.objects.get(username=ticket.assigned_to)
                Notification.objects.create(
                    title=f'Ticket deleted',
                    text=f'The ticket "{ticket.title}" you were assigned to was deleted by {self.request.user.username}',
                    recipient=user
                )
            manager_id = Project.objects.filter(title=ticket.project).values_list('project_manager', flat=True)[0]
            if manager_id is not None:
                user_id = Member.objects.filter(id=manager_id).values_list('user_id', flat=True)[0]
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    title=f'Ticket deleted',
                    text=f'{self.request.user.username} deleted "{ticket.title}" ticket from "{ticket.project}" project',
                    recipient=user
                )
            return super(TicketDeleteView, self).form_valid(form)
        return super(TicketDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse("tickets:ticket-list")


class AssignMemberView(OrganizerAndLoginRequiredMixin, generic.FormView):
    template_name = "tickets/assign_member.html"
    form_class = AssignMemberForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignMemberView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("tickets:ticket-list")

    def form_valid(self, form):
        member = form.cleaned_data["member"]
        ticket = Ticket.objects.get(id=self.kwargs["pk"])
        ticket.assigned_to = member
        ticket.save()
        user = User.objects.get(username=ticket.assigned_to)
        Notification.objects.create(
            title=f'New ticket',
            text=f'"{ticket.title}" ticket was assigned to you by {self.request.user.username}',
            recipient=user
        )
        return super(AssignMemberView, self).form_valid(form)

class StatusListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "tickets/status_list.html"
    context_object_name = "status_list"

    def get_context_data(self, **kwargs):
        context = super(StatusListView, self).get_context_data(**kwargs)
        user = self.request.user
        project = Project.objects.filter(organisation=user.account, archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        color_code = Status.objects.filter(organisation=user.account).values_list('color_code', flat=True)
        status_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False, project__in=project).values('status_id').annotate(total=Count('status_id'))
        status_ids = [st['status_id'] for st in status_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(status__isnull=True).count(),
            "color_code": color_code,
            "status_ids": status_ids,
            "status_counts": status_counts,
        })
        return context


    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Status.objects.filter(organisation=user.account)
        else:
            queryset = Status.objects.filter(organisation=user.member.organisation)
        return queryset

class StatusDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/status_detail.html"
    context_object_name = "status"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Status.objects.filter(organisation=user.account)
        else:
            queryset = Status.objects.filter(organisation=user.member.organisation)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(StatusDetailView, self).get_context_data(**kwargs)
        project = Project.objects.filter(archive=False)
        context["tickets"] = Ticket.objects.filter(organisation=user.account, project__in=project)
        return context

class StatusCreateView(OrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/status_create.html"
    form_class = StatusModelForm

    def get_success_url(self):
        return reverse("tickets:status-list")
    def form_valid(self, form):
        status = form.save(commit=False)
        status.organisation = self.request.user.account
        color_code_client = self.request.POST['CI']
        status.color_code = color_code_client
        status.save()
        return super(StatusCreateView, self).form_valid(form)

class StatusUpdateView(OrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/status_update.html"
    form_class = StatusModelForm

    def get_success_url(self):
        return reverse("tickets:status-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Status.objects.filter(organisation=user.account)
        else:
            queryset = Status.objects.filter(organisation=user.member.organisation)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(StatusUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(StatusUpdateView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organizer:
            queryset = Status.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        else:
            queryset = Status.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        print(queryset)
        context.update({
            "color_code": queryset[0],
        })
        return context


class StatusDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/status_delete.html"

    def get_success_url(self):
        return reverse("tickets:status-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Status.objects.filter(organisation=user.account)
        else:
            queryset = Status.objects.filter(organisation=user.member.organisation)
        return queryset

class TicketCategoryUpdateView(NotManagerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/ticket_status_update.html"
    form_class = TicketSatusUpdateForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TicketCategoryUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user)

        return queryset

    def form_valid(self, form):
        status = form.cleaned_data['status']
        test_status = Status.objects.filter(name=status).values_list('test_status', flat=True)[0]
        if test_status:
            id = self.kwargs["pk"]
            ticket = Ticket.objects.get(id=id)
            project_id = Ticket.objects.filter(id=id).values_list('project', flat=True)[0]
            project = Project.objects.filter(id=project_id)
            users = User.objects.filter(ticket_flow__in=project, role='tester')
            project = Project.objects.get(id=project_id)
            if len(users) != 0:
                for user in users:
                    Notification.objects.create(
                        title=f'Test ticket',
                        text=f'"{ticket.title}" is in your "{project.title}" project and ready for a test',
                        recipient=user
                    )
        return super(TicketCategoryUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse("tickets:ticket-list")




class PriorityListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "tickets/priority_list.html"
    context_object_name = "priority_list"

    def get_context_data(self, **kwargs):
        context = super(PriorityListView, self).get_context_data(**kwargs)
        user = self.request.user
        project = Project.objects.filter(organisation=user.account, archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        color_code = Priority.objects.filter(organisation=user.account).values_list('color_code', flat=True)
        priority_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False, project__in=project).values('priority_id').annotate(total=Count('priority_id'))
        priority_ids = [pr['priority_id'] for pr in priority_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(priority__isnull=True).count(),
            "color_code": color_code,
            "priority_ids": priority_ids,
            "priority_counts": priority_counts,
        })
        return context


    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Priority.objects.filter(organisation=user.account)
        else:
            queryset = Priority.objects.filter(organisation=user.member.organisation)
        return queryset

class PriorityDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/priority_detail.html"
    context_object_name = "priority"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Priority.objects.filter(organisation=user.account)
        else:
            queryset = Priority.objects.filter(organisation=user.member.organisation)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(PriorityDetailView, self).get_context_data(**kwargs)
        project = Project.objects.filter(archive=False)
        context["tickets"] = Ticket.objects.filter(organisation=user.account, project__in=project)
        return context


class PriorityCreateView(OrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/priority_create.html"
    form_class = PriorityModelForm

    def get_success_url(self):
        return reverse("tickets:priority-list")

    def form_valid(self, form):
        priority = form.save(commit=False)
        priority.organisation = self.request.user.account
        color_code_client = self.request.POST['CI']
        priority.color_code = color_code_client
        priority.save()
        return super(PriorityCreateView, self).form_valid(form)

class PriorityUpdateView(OrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/priority_update.html"
    form_class = PriorityModelForm

    def get_success_url(self):
        return reverse("tickets:priority-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Priority.objects.filter(organisation=user.account)
        else:
            queryset = Priority.objects.filter(organisation=user.member.organisation)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(PriorityUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(PriorityUpdateView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organizer:
            queryset = Priority.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        else:
            queryset = Priority.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        print(queryset)
        context.update({
            "color_code": queryset[0],
        })
        return context
class PriorityDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/priority_delete.html"

    def get_success_url(self):
        return reverse("tickets:priority-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Priority.objects.filter(organisation=user.account)
        else:
            queryset = Priority.objects.filter(organisation=user.member.organisation)
        return queryset

class TypeListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "tickets/type_list.html"
    context_object_name = "type_list"

    def get_context_data(self, **kwargs):
        context = super(TypeListView, self).get_context_data(**kwargs)
        user = self.request.user
        project = Project.objects.filter(organisation=user.account, archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        color_code = Type.objects.filter(organisation=user.account).values_list('color_code', flat=True)
        type_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False,project__in=project).values('type_id').annotate(total=Count('type_id'))
        type_ids = [tp['type_id'] for tp in type_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(type__isnull=True).count(),
            "color_code": color_code,
            "type_ids": type_ids,
            "type_counts": type_counts,
        })
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Type.objects.filter(organisation=user.account)
        else:
            queryset = Type.objects.filter(organisation=user.member.organisation)
        return queryset

class TypeDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/type_detail.html"
    context_object_name = "type"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Type.objects.filter(organisation=user.account)
        else:
            queryset = Type.objects.filter(organisation=user.member.organisation)
        return queryset

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(TypeDetailView, self).get_context_data(**kwargs)
        project = Project.objects.filter(archive=False)
        context["tickets"] = Ticket.objects.filter(organisation=user.account, project__in=project)
        return context

class TypeCreateView(OrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/type_create.html"
    form_class = TypeModelForm

    def get_success_url(self):
        return reverse("tickets:type-list")

    def form_valid(self, form):
        type = form.save(commit=False)
        type.organisation = self.request.user.account
        color_code_client = self.request.POST['CI']
        type.color_code = color_code_client
        type.save()
        return super(TypeCreateView, self).form_valid(form)

class TypeUpdateView(OrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/type_update.html"
    form_class = TypeModelForm

    def get_success_url(self):
        return reverse("tickets:type-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Type.objects.filter(organisation=user.account)
        else:
            queryset = Type.objects.filter(organisation=user.member.organisation)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(TypeUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(TypeUpdateView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organizer:
            queryset = Type.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        else:
            queryset = Type.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('color_code', flat=True)
        context.update({
            "color_code": queryset[0],
        })
        return context

class TypeDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/type_delete.html"

    def get_success_url(self):
        return reverse("tickets:type-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Type.objects.filter(organisation=user.account)
        else:
            queryset = Type.objects.filter(organisation=user.member.organisation)
        return queryset

class CommentCreateView(NotManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("tickets:ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super(CommentCreateView, self).get_context_data(**kwargs)
        context.update({
            "ticket": Ticket.objects.get(pk=self.kwargs["pk"]),
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
            user = User.objects.get(username=ticket.assigned_to)
            Notification.objects.create(
                title=f'New comment',
                text=f'There is a new comment created for "{ticket.title}" ticket by {self.request.user.username}',
                recipient=user
            )
        return super(CommentCreateView, self).form_valid(form)

class CommentUpdateView(CommentAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/comment_update.html"
    form_class = CommentModelForm

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Comment.objects.filter(ticket__organisation=user.account)
        else:
            queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset

    def get_success_url(self):
        return reverse("tickets:ticket-detail",  kwargs={"pk": self.get_object().ticket.id})

class CommentDeleteView(CommentAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/comment_delete.html"

    def get_success_url(self):
        comment = Comment.objects.get(id=self.kwargs["pk"])
        return reverse("tickets:ticket-detail", kwargs={"pk": comment.ticket.pk})

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            queryset = Comment.objects.filter(ticket__organisation=user.account)
        else:
            queryset = Comment.objects.filter(ticket__organisation=user.member.organisation)
        return queryset

class TicketJsonView(OrganizerAndLoginRequiredMixin,generic.View):
    def get(self, request, *args, **kwargs):
        user = self.request.user
        project = Project.objects.filter(organisation=user.account, archive=False)
        qs = list(Ticket.objects.filter(project__in=project).values())
        return JsonResponse({
            "qs": qs,
        })


