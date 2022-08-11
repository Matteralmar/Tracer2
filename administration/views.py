import random
from django.core.mail import send_mail
from django.shortcuts import render, reverse, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.models import *
from .forms import *
from .mixins import *
from django.db.models import Q




class MemberListView(ManagerOrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "administration/member_list.html"
    context_object_name = "members"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user = User.objects.filter(member__organisation=user.account)
        else:
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), member__organisation=user.member.organisation,ticket_flow__in=queryset).distinct()
        return user


class MemberCreateView(ManagerOrganizerAndLoginRequiredMixin, generic.CreateView):
    template_name = "administration/member_create.html"
    form_class = MemberModelForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(MemberCreateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("administration:member-list")

    def form_valid(self, form):
        usr = self.request.user
        user = form.save(commit=False)
        user.is_member = True
        user.is_organizer = False
        user.set_password(f"{random.randint(0, 1000000)}")
        user.save()
        if usr.is_organizer:
            Member.objects.create(
                user=user,
                organisation=self.request.user.account,
            )
        else:
            Member.objects.create(
                user=user,
                organisation=self.request.user.member.organisation,
            )

        Notification.objects.create(
            title=f'Welcome to Tracer',
            text=f'You was invited by {self.request.user} to a team. Hope you will enjoy your work in our app!',
            recipient=user
        )
        if usr.role == 'project_manager':
            recipient = User.objects.get(username=usr.member.organisation)
            Notification.objects.create(
                title=f'New user',
                text=f'User "{user.username}" was created by {self.request.user}',
                recipient=recipient
            )
        send_mail(
            subject="Tracer: You are invited to be a member",
            message="You were added as a member of a team. Please reset your password with your email and login to start your work.",
            from_email="noreply@mg.mytrac-api.xyz",
            recipient_list=[user.email]
        )
        return super(MemberCreateView, self).form_valid(form)

class MemberDetailView(ManagerOrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "administration/member_detail.html"
    context_object_name = "member"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user = User.objects.filter(member__organisation=user.account)
        else:
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), member__organisation=user.member.organisation,ticket_flow__in=queryset).distinct()
        return user

class MemberUpdateView(ManagerOrganizerAndLoginRequiredMixin, generic.UpdateView):
    template_name = "administration/member_update.html"
    form_class = MemberModelForm
    context_object_name = "member"

    def get_form_kwargs(self, **kwargs):
        kwargs = super(MemberUpdateView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_context_data(self, **kwargs):
        user = User.objects.get(pk=self.kwargs["pk"])
        context = super(MemberUpdateView, self).get_context_data(**kwargs)
        context["user"] = user
        return context

    def form_valid(self, form):
        usr = User.objects.get(pk=self.kwargs["pk"])
        username = form.cleaned_data['username']
        role = form.cleaned_data['role']
        ticket_flow = form.cleaned_data['ticket_flow']
        proj = usr.ticket_flow.all()
        if role != usr.role:
            usr.role = role
            usr.save()
            Notification.objects.create(
                title=f'Role change',
                text=f'Your role was changed to "{usr.get_role_display()}" by {self.request.user.username}',
                recipient=usr
            )
            if usr.role == 'developer':
                tickets = Ticket.objects.filter(assigned_to__user_id=usr.id, project__archive=False).update(assigned_to=None, author=self.request.user)

            if usr.role == 'tester':
                tickets = Ticket.objects.filter(author=usr, project__archive=False).update(author=self.request.user)

            if usr.role == 'project_manager':
                project = Project.objects.filter(project_manager__user=usr, archive=False).update(project_manager=None)

        if list(ticket_flow) != list(proj):
            if usr.role != 'project_manager':
                Notification.objects.create(
                    title=f'Ticket flow change',
                    text=f'Your ticket flow was altered by {self.request.user.username}',
                    recipient=usr
                )
                qs_difference = proj.difference(ticket_flow).values_list('id', flat=True)
                ticket = Ticket.objects.filter(assigned_to__user_id=usr.id, project__archive=False, project__in=qs_difference).update(assigned_to=None, author=self.request.user)

        if self.request.user.role == 'project_manager':
            user = User.objects.get(username=self.request.user.member.organisation)
            Notification.objects.create(
                title=f'User update',
                text=f'User "{username}" was updated by {self.request.user.username}',
                recipient=user
            )

        return super(MemberUpdateView, self).form_valid(form)

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user = User.objects.filter(member__organisation=user.account)
        else:
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), member__organisation=user.member.organisation, ticket_flow__in=queryset).distinct()
        return user

    def get_success_url(self):
        return reverse("administration:member-list")

class MemberRequestDeleteView(ManagerAndLoginRequiredMixin, generic.TemplateView):
    template_name = "administration/member_request_delete.html"

    def post(self, request, *args, **kwargs):
        user = self.request.user
        project = Project.objects.filter(project_manager__user=user, archive=False)
        usr = get_object_or_404(User, ~Q(role='project_manager'), member__organisation=user.member.organisation, ticket_flow__in=project, id=self.kwargs["pk"])
        user = User.objects.get(username=user.member.organisation)
        Notification.objects.create(
            title=f'Request Delete',
            text=f'{self.request.user.username} requested a deletion of "{usr.username}" member. Please contact {self.request.user.username} for more details.',
            recipient=user
        )
        return redirect("administration:member-list")

class MemberDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "administration/member_delete.html"
    context_object_name = "member"

    def get_success_url(self):
        return reverse("administration:member-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user = User.objects.filter(member__organisation=user.account)
        else:
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), member__organisation=user.member.organisation, ticket_flow__in=queryset).distinct()
        return user



