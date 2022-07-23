import random
from django.core.mail import send_mail
from django.shortcuts import render, reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.models import *
from .forms import *
from .mixins import *




class MemberListView(ManagerOrganizerAndLoginRequiredMixin, generic.ListView):
    template_name = "administration/member_list.html"
    context_object_name = "members"

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True)
        else:
            id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True)
        return User.objects.filter(pk__in=id)


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

        send_mail(
            subject="You are invited to be a member",
            message="You were added as a member of a team. Please login to start working",
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
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True).distinct()
        return User.objects.filter(pk__in=user_id)

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
        user = User.objects.get(pk=self.kwargs["pk"])
        ticket_flow = form.cleaned_data['ticket_flow']
        role = form.cleaned_data['role']
        if role != user.role:
            user = User.objects.get(username=user.username)
            Notification.objects.create(
                title=f'Role',
                text=f'Your role was changed to "{role}" by {self.request.user.username}',
                recipient=user
            )
        if user.ticket_flow != ticket_flow:
            user = User.objects.get(username=user.username)
            Notification.objects.create(
                title=f'Ticket flow',
                text=f'Your ticket flow was altered to "{ticket_flow}" by {self.request.user.username}',
                recipient=user
            )
        return super(MemberUpdateView, self).form_valid(form)

    def get_queryset(self):
        user = self.request.user
        if user.is_organizer:
            user_id = Member.objects.filter(organisation=user.account).values_list('user_id', flat=True).distinct()
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id', flat=True).distinct()
        return User.objects.filter(pk__in=user_id)

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
        else:
            user_id = Member.objects.filter(organisation=user.member.organisation).values_list('user_id',flat=True).distinct()
        return User.objects.filter(pk__in=user_id)

