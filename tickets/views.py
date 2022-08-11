from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.shortcuts import render, reverse, render, get_object_or_404
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
        project = Project.objects.filter(archive=False)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
            queryset = queryset.filter(~Q(status_id__in=status_id), assigned_to__user=user)
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
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        elif user.role == 'developer':
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(~Q(status_id__in=status_id), assigned_to__user=user)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, author=user, project__in=project)
        return queryset


class TicketCreateView(NotManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/ticket_create.html"
    form_class = TicketCreateModelForm

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
        titl = form.cleaned_data['title']
        if user.role != 'developer':
            assigned_to = form.cleaned_data['assigned_to']
            project = form.cleaned_data['project']
            if assigned_to is not None:
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'You was assigned a new "{titl}" ticket by {self.request.user.username}',
                    recipient=assigned_to.user
                )

            if project.project_manager is not None:
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'{self.request.user.username} created "{titl}" ticket for "{project}" project',
                    recipient=project.project_manager.user
                )
            return super(TicketCreateView, self).form_valid(form)
        else:
            project = form.cleaned_data['project']
            if project.project_manager is not None:
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'{self.request.user.username} created "{titl}" ticket for "{project}" project',
                    recipient=project.project_manager.user
                )
            return super(TicketCreateView, self).form_valid(form)


class TicketUpdateView(OrgDevAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/ticket_update.html"
    form_class = TicketUpdateModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TicketUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
        if user.is_organizer:
            queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        else:
            queryset = Ticket.objects.filter(organisation=user.member.organisation, project__in=project)
            queryset = queryset.filter(~Q(status_id__in=status_id), assigned_to__user=user)
        return queryset


    def get_success_url(self):
        return reverse("tickets:ticket-list")

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(TicketUpdateView, self).get_context_data(**kwargs)
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        context["ticket"] = ticket
        return context


    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if user.is_organizer:
            titl = form.cleaned_data['title']
            assigned_to = form.cleaned_data['assigned_to']
            project = form.cleaned_data['project']
            if (assigned_to and ticket.assigned_to is not None) and (assigned_to == ticket.assigned_to):
                Notification.objects.create(
                    title=f'Ticket update',
                    text=f'Your "{titl}" ticket details was updated by {self.request.user.username}',
                    recipient=ticket.assigned_to.user
                )
            if (assigned_to and ticket.assigned_to is not None) and (assigned_to != ticket.assigned_to):
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'"{titl}" ticket was assigned to you by {self.request.user.username}',
                    recipient=assigned_to.user
                )
                Notification.objects.create(
                    title=f'Unassigned ticket',
                    text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}',
                    recipient=ticket.assigned_to.user
                )
            if ticket.assigned_to is None and assigned_to is not None:
                Notification.objects.create(
                    title=f'New ticket',
                    text=f'"{titl}" ticket was assigned to you by {self.request.user.username}',
                    recipient=assigned_to.user
                )
            if ticket.assigned_to is not None and assigned_to is None:
                Notification.objects.create(
                    title=f'Unassigned ticket',
                    text=f'"{ticket.title}" ticket was unassigned from you by {self.request.user.username}',
                    recipient=ticket.assigned_to.user
                )
            if (project and ticket.project is not None) and (project == ticket.project):
                if project.project_manager is not None:
                    Notification.objects.create(
                        title=f'Ticket update',
                        text=f'{self.request.user.username} updated "{titl}" ticket for "{project}" project',
                        recipient=ticket.project.project_manager.user
                    )
            if (project and ticket.project is not None) and (project != ticket.project):
                Notification.objects.create(
                        title=f'New ticket',
                        text=f'"{titl}" ticket was assigned to your "{project}" project by {self.request.user.username}',
                        recipient=project.project_manager.user
                    )

                Notification.objects.create(
                        title=f'Unassigned ticket',
                        text=f'"{ticket.title}" ticket was unassigned from your "{ticket.project}" project by {self.request.user.username}',
                        recipient=ticket.project.project_manager.user
                    )

            if titl != ticket.title:
                if ticket.assigned_to is not None and ticket.assigned_to == assigned_to:
                    Notification.objects.create(
                        title=f'Ticket name change',
                        text=f'There was a name change of "{ticket.title}" into "{titl}" by {self.request.user.username}',
                        recipient=ticket.assigned_to.user
                    )

                if ticket.project.project_manager is not None and project == ticket.project:
                    Notification.objects.create(
                        title=f'Ticket name change',
                        text=f'There was a name change of "{ticket.title}" into "{titl}" ticket from your "{ticket.project}" project by {self.request.user.username}',
                        recipient=ticket.project.project_manager.user
                    )

        if user.role == 'developer':
            status = form.cleaned_data['status']
            if ticket.project.project_manager is not None:
                if status is not None and status.test_status:
                    ticket = Ticket.objects.get(id=self.kwargs["pk"])
                    if ticket.project.project_manager.user is not None:
                        Notification.objects.create(
                            title=f'Test ticket',
                            text=f'"{ticket.title}" is in your "{ticket.project}" project ready for a test',
                            recipient=ticket.project.project_manager.user
                        )
                    return super(TicketUpdateView, self).form_valid(form)
                Notification.objects.create(
                    title=f'Ticket update',
                    text=f'{self.request.user.username} updated "{ticket.title}" ticket for "{ticket.project}" project',
                    recipient=ticket.project.project_manager.user
                )

        return super(TicketUpdateView, self).form_valid(form)


class TicketDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/ticket_delete.html"

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        return queryset

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if user.role != 'developer':
            if ticket.assigned_to is not None:
                Notification.objects.create(
                    title=f'Ticket deleted',
                    text=f'The ticket "{ticket.title}" you were assigned to was deleted by {self.request.user.username}',
                    recipient=ticket.assigned_to.user
                )

        if ticket.project.project_manager is not None:
            Notification.objects.create(
                title=f'Ticket deleted',
                text=f'{self.request.user.username} deleted "{ticket.title}" ticket from "{ticket.project}" project',
                recipient=ticket.project.project_manager.user
            )
        return super(TicketDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse("tickets:ticket-list")

class TicketRequestChangeView(TstrDevAndLoginRequiredMixin, generic.TemplateView):
    template_name = "tickets/ticket_request_change.html"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        project = Project.objects.filter(organisation=user.member.organisation, archive=False)
        if user.role == 'tester':
            ticket = get_object_or_404(Ticket, author=user, project__in=project, pk=self.kwargs["pk"])
        else:
            status_id = Status.objects.filter(test_status=True).values_list('id', flat=True)
            member = Member.objects.get(user_id=user.id)
            ticket = get_object_or_404(Ticket, ~Q(status_id__in=status_id), assigned_to=member, project__in=project, pk=self.kwargs["pk"])
        if ticket.project.project_manager is not None:
            Notification.objects.create(
                title=f'Request Change',
                text=f'{self.request.user.username} requested a change to "{ticket.title}" ticket. Please contact {self.request.user.username} for more details.',
                recipient=ticket.project.project_manager.user
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
        status_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False, project__in=project).values('status_id').annotate(total=Count('status_id'))
        status_ids = [st['status_id'] for st in status_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(status__isnull=True).count(),
            "status_ids": status_ids,
            "status_counts": status_counts,
        })
        return context


    def get_queryset(self):
        user = self.request.user
        queryset = Status.objects.filter(organisation=user.account)
        return queryset

class StatusDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/status_detail.html"
    context_object_name = "status"

    def get_queryset(self):
        user = self.request.user
        queryset = Status.objects.filter(organisation=user.account)
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
    context_object_name = "status"

    def get_success_url(self):
        return reverse("tickets:status-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Status.objects.filter(organisation=user.account)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(StatusUpdateView, self).form_valid(form)



class StatusDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/status_delete.html"

    def get_success_url(self):
        return reverse("tickets:status-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Status.objects.filter(organisation=user.account)
        return queryset


class TicketCategoryUpdateView(OrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/ticket_category_update.html"
    form_class = TicketCategoryUpdateForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TicketCategoryUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        project = Project.objects.filter(archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        return queryset

    def form_valid(self, form):
        id = self.kwargs["pk"]
        ticket = Ticket.objects.get(id=id)
        status = form.cleaned_data['status']
        if status is not None and status.test_status and ticket.status != status:
            if ticket.project.project_manager is not None:
                Notification.objects.create(
                    title=f'Test ticket',
                    text=f'"{ticket.title}" is in your "{ticket.project.title}" project ready for a test',
                    recipient=ticket.project.project_manager.user
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
        priority_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False, project__in=project).values('priority_id').annotate(total=Count('priority_id'))
        priority_ids = [pr['priority_id'] for pr in priority_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(priority__isnull=True).count(),
            "priority_ids": priority_ids,
            "priority_counts": priority_counts,
        })
        return context


    def get_queryset(self):
        user = self.request.user
        queryset = Priority.objects.filter(organisation=user.account)
        return queryset

class PriorityDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/priority_detail.html"
    context_object_name = "priority"

    def get_queryset(self):
        user = self.request.user
        queryset = Priority.objects.filter(organisation=user.account)
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
    context_object_name = "priority"

    def get_success_url(self):
        return reverse("tickets:priority-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Priority.objects.filter(organisation=user.account)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(PriorityUpdateView, self).form_valid(form)


class PriorityDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/priority_delete.html"

    def get_success_url(self):
        return reverse("tickets:priority-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Priority.objects.filter(organisation=user.account)
        return queryset

class TypeListView(OrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "tickets/type_list.html"
    context_object_name = "type_list"

    def get_context_data(self, **kwargs):
        context = super(TypeListView, self).get_context_data(**kwargs)
        user = self.request.user
        project = Project.objects.filter(organisation=user.account, archive=False)
        queryset = Ticket.objects.filter(organisation=user.account, project__in=project)
        type_counts = Ticket.objects.filter(organisation=user.account, status_id__isnull=False,project__in=project).values('type_id').annotate(total=Count('type_id'))
        type_ids = [tp['type_id'] for tp in type_counts]
        context.update({
            "unassigned_ticket_count": queryset.filter(type__isnull=True).count(),
            "type_ids": type_ids,
            "type_counts": type_counts,
        })
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = Type.objects.filter(organisation=user.account)
        return queryset

class TypeDetailView(OrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "tickets/type_detail.html"
    context_object_name = "type"

    def get_queryset(self):
        user = self.request.user
        queryset = Type.objects.filter(organisation=user.account)
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
    context_object_name = "type"

    def get_success_url(self):
        return reverse("tickets:type-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Type.objects.filter(organisation=user.account)
        return queryset

    def form_valid(self, form):
        color_data = form.save(commit=False)
        color_code_client = self.request.POST['CI']
        color_data.color_code = color_code_client
        return super(TypeUpdateView, self).form_valid(form)


class TypeDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "tickets/type_delete.html"

    def get_success_url(self):
        return reverse("tickets:type-list")

    def get_queryset(self):
        user = self.request.user
        queryset = Type.objects.filter(organisation=user.account)
        return queryset


class CommentCreateView(NotManagerAndLoginRequiredMixin, generic.CreateView):
    template_name = "tickets/comment_create.html"
    form_class = CommentModelForm

    def get_success_url(self):
        return reverse("tickets:ticket-detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(CommentCreateView, self).get_context_data(**kwargs)
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if user.is_organizer:
            project = get_object_or_404(Project, organisation=user.account, archive=False, title=ticket.project.title)
        else:
            project = get_object_or_404(Project, organisation=user.member.organisation, archive=False, title=ticket.project.title)
        context.update({
            "ticket": ticket,
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.save()
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        if ticket.assigned_to is not None:
            if user.role != 'developer':
                Notification.objects.create(
                    title=f'New comment',
                    text=f'There is a new comment created for "{ticket.title}" ticket by {self.request.user.username}',
                    recipient=ticket.assigned_to.user
                )
        return super(CommentCreateView, self).form_valid(form)

class CommentUpdateView(CommentAndLoginRequiredMixin, generic.UpdateView):
    template_name = "tickets/comment_update.html"
    form_class = CommentModelForm
    context_object_name = "comment"

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
            proj = list(request.user.ticket_flow.all())
            qs = qs.filter(title__in=proj, archive=False)
            ctx["projects"] = list(qs.values())
            return JsonResponse(ctx)

        if request.user.is_organizer:
            result = User.objects.get(member__id=filtr)
            proj = list(result.ticket_flow.all())
            qs = qs.filter(title__in=proj, archive=False)

        if request.user.role == 'tester':
            result = User.objects.get(member__id=filtr)
            proj_1 = list(result.ticket_flow.all())
            proj_2 = list(request.user.ticket_flow.all())
            qs = qs.filter(title__in=proj_1, archive=False) & Project.objects.filter(title__in=proj_2,archive=False)

        ctx["projects"] = list(qs.values())

    if name == 'project':
        if request.user.is_organizer:
            members = Member.objects.filter(organisation=request.user.account)
        else:
            members = Member.objects.filter(organisation=request.user.member.organisation)

        if filtr == '' and request.user.is_organizer:
            qs = User.objects.filter(member__in=members, role='developer')
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
            return JsonResponse(ctx)

        if filtr == '' and request.user.is_member:
            proj = list(request.user.ticket_flow.all())
            project = Project.objects.filter(title__in=proj, archive=False)
            qs = User.objects.filter(member__in=members, role='developer', ticket_flow__in=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)
            return JsonResponse(ctx)

        project = Project.objects.get(id=filtr, archive=False)

        if request.user.is_organizer:
            qs = User.objects.filter(member__in=members, role='developer', ticket_flow=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)

        if request.user.role == 'tester':
            qs = User.objects.filter(member__in=members, role='developer', ticket_flow=project).distinct()
            qs = qs.select_related('member').values('member', 'username')
            ctx["users"] = list(qs)

    return JsonResponse(ctx)
