import random
from django.core.mail import send_mail
from django.shortcuts import render, reverse
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
            id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True)
            user = User.objects.filter(pk__in=id)
        else:
            id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True)
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(pk__in=id, ticket_flow__in=queryset).distinct()
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
        user_s = self.request.user
        user = form.save(commit=False)
        user.is_member = True
        user.is_organizer = False
        user.set_password(f"{random.randint(0, 1000000)}")
        user.save()
        if user_s.is_organizer:
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
        if user_s.role == 'project_manager':
            recipient = User.objects.get(id=user_s.member.organisation.id)
            Notification.objects.create(
                title=f'New user',
                text=f'User "{user.username}" was created by {self.request.user}',
                recipient=recipient
            )
        send_mail(
            subject="You are invited to be a member",
            message="You were added as a member of a team. Please reset your password with your email and login to start your work.",
            from_email="ultramacflaw@gmail.com",
            recipient_list=[user.email]
        )
        return super(MemberCreateView, self).form_valid(form)

class MemberDetailView(ManagerOrganizerAndLoginRequiredMixin, generic.DetailView):
    template_name = "administration/member_detail.html"
    context_object_name = "member"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user_id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True).distinct()
            user = User.objects.filter(pk__in=user_id)
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True).distinct()
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), pk__in=user_id, ticket_flow__in=queryset).distinct()
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

    def form_valid(self, form):
        user = form.save(commit=False)
        user_c = User.objects.get(pk=self.kwargs["pk"])
        role = form.cleaned_data['role']
        ticket_flow = form.cleaned_data['ticket_flow']
        results = User.objects.filter(pk=self.kwargs["pk"])
        for usr in results:
            proj = usr.ticket_flow.all()
        if role != user_c.role:
            user = User.objects.get(username=user_c.username)
            if user_c.role == 'developer':
                member = Member.objects.get(user_id=user.id)
                tickets = Ticket.objects.filter(assigned_to=member).update(assigned_to=None, author=self.request.user)
            Notification.objects.create(
                title=f'Role change',
                text=f'Your role was changed to "{user.get_role_display()}" by {self.request.user.username}',
                recipient=user
            )
            user.save()
        if list(ticket_flow) != list(proj):
            Notification.objects.create(
                title=f'Ticket flow change',
                text=f'Your ticket flow was altered by {self.request.user.username}',
                recipient=user_c
            )
            qs_difference = proj.difference(ticket_flow).values_list('id', flat=True)
            member = Member.objects.get(user_id=user_c.id)
            ticket = Ticket.objects.filter(assigned_to=member, project_id__in=qs_difference).update(assigned_to=None, author=self.request.user)

        if self.request.user.role == 'project_manager':
            user = User.objects.get(username=self.request.user.member.organisation)
            Notification.objects.create(
                title=f'User update',
                text=f'User "{user_c}" was updated by {self.request.user.username}',
                recipient=user
            )

        return super(MemberUpdateView, self).form_valid(form)

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user_id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True).distinct()
            user = User.objects.filter(pk__in=user_id)
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True).distinct()
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), pk__in=user_id, ticket_flow__in=queryset).distinct()
        return user

    def get_success_url(self):
        return reverse("administration:member-list")


class MemberDeleteView(OrganizerAndLoginRequiredMixin, generic.DeleteView):
    template_name = "administration/member_delete.html"
    context_object_name = "member"

    def get_success_url(self):
        return reverse("administration:member-list")

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user_id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True).distinct()
            user = User.objects.filter(pk__in=user_id)
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True).distinct()
            queryset = Project.objects.filter(project_manager__user=user, archive=False)
            user = User.objects.filter(~Q(role='project_manager'), pk__in=user_id, ticket_flow__in=queryset).distinct()
        return user


