from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, Http404
from django.views import generic, View
from .models import *
from .forms import *
from administration.mixins import *
from django.db.models import Count, Q

from .tokens import account_activation_token
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from django.contrib.auth import login
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        username = form.cleaned_data['username']
        user = User.objects.get(username=username)
        Notification.objects.create(
            title=f'Welcome to Tracer',
            text=f'Hello {username}, hope you will enjoy your work using our app!',
            recipient=user
        )
        current_site = get_current_site(self.request)
        subject = 'Activate your Tracer account'
        message = render_to_string('registration/email_activation.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject, message)

        messages.info(self.request, ('Please confirm your email to complete registration.'))

        return super(SignupView, self).form_valid(form)

    def get_success_url(self):
        return reverse("login")

class ActivateAccount(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.email_confirmed = True
            user.save()
            login(request, user)
            return redirect('dashboard:dashboard-chart')
        else:
            messages.warning(request, ('The confirmation link was invalid, possibly because it has already been used.'))
            return redirect('login')

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
            project = Project.objects.filter(organisation=user.account, archive=False)
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            project = Project.objects.filter(organisation=user.member.organisation, archive=False)
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            project = Project.objects.filter(organisation=user.member.organisation, archive=False)
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)
        return queryset


class TicketDetailView(NotManagerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/tickets_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)
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
        project = Project.objects.filter(archive=False)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)
        return queryset


    def get_success_url(self):
        return reverse("tickets:ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(TicketUpdateView, self).get_context_data(**kwargs)
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        context["ticket"] = ticket
        return context


    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        titl = form.cleaned_data['title']
        assigned_to = form.cleaned_data['assigned_to']
        project = form.cleaned_data['project']
        if ticket.title != titl:
            if user.role != 'developer':
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
                    text=f'There was a name change of "{ticket.title}" into "{titl}" ticket from your "{ticket.project}" project by {self.request.user.username}',
                    recipient=user
                )
        if user.role != 'developer':
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
                    text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}',
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
                    text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}',
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
                    text=f'"{ticket.title}" ticket was unassigned from your "{ticket.project}" project by {self.request.user.username}',
                    recipient=user
                )
            return super(TicketUpdateView, self).form_valid(form)
        return super(TicketUpdateView, self).form_valid(form)


class TicketDeleteView(NotManagerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/ticket_delete.html"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(assigned_to__user=user, author=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)
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

class TicketRequestDeleteView(DeveloperAndLoginRequiredMixin, generic.TemplateView):
    template_name = "tickets/ticket_request_delete.html"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        member = Member.objects.get(user_id=user.id)
        project = Project.objects.filter(organisation=user.member.organisation, archive=False)
        ticket = Ticket.objects.get(project__in=project, pk=self.kwargs["pk"], assigned_to=member)
        user = User.objects.get(tickets=ticket)
        Notification.objects.create(
            title=f'Deletion Request',
            text=f'{self.request.user.username} requested to delete "{ticket.title}" ticket.',
            recipient=user
        )
        return redirect("tickets:ticket-list")


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
        project = Project.objects.filter(archive=False)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)

        return queryset

    def form_valid(self, form):
        status = form.cleaned_data['status']
        test_status = Status.objects.filter(name=status).values_list('test_status', flat=True)
        if self.request.user.role != 'tester':
            if len(test_status) != 0 and test_status[0]:
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
        user = self.request.user
        if user.is_organizer:
            project = Project.objects.filter(organisation=user.account, archive=False).values_list('id', flat=True)
        else:
            project = Project.objects.filter(organisation=user.member.organisation, archive=False).values_list('id',flat=True)
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if ticket.project in project:
            raise Http404
        context.update({
            "ticket": ticket,
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        ticket = Ticket.objects.get(pk=self.kwargs["pk"], project__in=project)
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        if ticket.assigned_to is not None:
            if user.role != 'developer':
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

def filter_(request):
    ctx = {}
    filtr = request.POST.get("filter")
    name = request.POST.get("name")
    if name == 'assigned_to':
        if request.user.is_organizer:
            qs = Project.objects.filter(organisation=request.user.account, archive=False)
        else:
            qs = Project.objects.filter(organisation=request.user.member.organisation, archive=False)
        if filtr == '' and request.user.is_organizer:
            ctx["projects"] = list(qs.values())
            return JsonResponse(ctx)
        if filtr == '' and request.user.is_member:
            results = User.objects.filter(id=request.user.id)
            for usr in results:
                proj = list(usr.ticket_flow.all())
            qs = qs.filter(title__in=proj, archive=False)
            ctx["projects"] = list(qs.values())
            return JsonResponse(ctx)
        dev = int(Member.objects.filter(id=filtr).values_list('user_id', flat=True)[0])
        if request.user.is_organizer:
            results = User.objects.filter(id=dev)
            for usr in results:
                proj = list(usr.ticket_flow.all())
            qs = qs.filter(title__in=proj, archive=False)
        if request.user.role == 'tester':
            results = User.objects.filter(id=dev)
            for usr in results:
                proj_1 = list(usr.ticket_flow.all())
            results = User.objects.filter(id=request.user.id)
            for usr in results:
                proj_2 = list(usr.ticket_flow.all())
            qs = qs.filter(title__in=proj_1, archive=False) & Project.objects.filter(title__in=proj_2,archive=False)
        ctx["projects"] = list(qs.values())
    if name == 'project':
        if request.user.is_organizer:
            user_id = Member.objects.filter(organisation=request.user.account).values_list('user_id', flat=True)
        else:
            user_id = Member.objects.filter(organisation=request.user.member.organisation).values_list('user_id', flat=True)
        if filtr == '' and request.user.is_organizer:
            qs = User.objects.filter(id__in=user_id, role='developer')
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
            return JsonResponse(ctx)
        if filtr == '' and request.user.is_member:
            results = User.objects.filter(id=request.user.id)
            for usr in results:
                proj = list(usr.ticket_flow.all())
            project = Project.objects.filter(title__in=proj, archive=False)
            qs = User.objects.filter(id__in=user_id, role='developer', ticket_flow__in=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
            return JsonResponse(ctx)
        project = Project.objects.get(id=filtr, archive=False)
        if request.user.is_organizer:
            qs = User.objects.filter(id__in=user_id, role='developer', ticket_flow=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
        if request.user.role == 'tester':
            qs = User.objects.filter(id__in=user_id, role='developer', ticket_flow=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
    return JsonResponse(ctx)
