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


class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

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
        print(self.request.POST.get("filter"))
        if self.request.POST.get("filter"):
            inp_value = self.request.GET['results']
            multiple_inp = Q(Q(title__icontains=inp_value)|Q(project__icontains=inp_value))
            if user.is_organizer:
                queryset = Ticket.objects.filter(multiple_inp, organisation=user.account, assigned_to__isnull=False)
            elif user.role == 'developer':
                queryset = Ticket.objects.filter(organisation=user.member.organisation, assigned_to__isnull=False)
                queryset = queryset.filter(multiple_inp, assigned_to__user=user)
            else:
                queryset = Ticket.objects.filter(multiple_inp, organisation=user.member.organisation, author=user)
        else:
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
            return super(TicketCreateView, self).form_valid(form)
        else:
            ticket = form.save(commit=False)
            ticket.organisation = user.member.organisation
            ticket.author = user
            ticket.save()
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

    def get_success_url(self):
        return reverse("tickets:ticket-list")

    def form_valid(self, form):
        user = self.request.user
        if user.is_organizer:
            status = Ticket.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('status', flat=True)[0]
        else:
            status = Ticket.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('status', flat=True)[0]
        try:
            status_id = int(self.request.POST['status'])
        except:
            status_id = None
        if user.is_organizer:
            email_disabled = Ticket.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('email_disable', flat=True)[0]
            project_id = Ticket.objects.filter(organisation=user.account, id=self.kwargs["pk"]).values_list('project_id', flat=True)
        else:
            email_disabled = Ticket.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('email_disable', flat=True)[0]
            project_id = Ticket.objects.filter(organisation=user.member.organisation, id=self.kwargs["pk"]).values_list('project_id', flat=True)
        project_manager_id = Project.objects.filter(pk__in=project_id).values_list('project_manager_id', flat=True)
        user_id = Member.objects.filter(pk__in=project_manager_id).values_list('user_id', flat=True)
        user_email = User.objects.filter(pk__in=user_id).values_list('email', flat=True)
        if len(user_email) == 0:
            user_email = "ultramacflaw@gmail.com"
        else:
            user_email = User.objects.filter(pk__in=user_id).values_list('email', flat=True)
        if status != status_id and email_disabled != True:
            send_mail(
                subject="Check for tickets status change",
                message="There is a change of status in project you managing. You can go and see it in your project table.",
                from_email="ultramacflaw@gmail.com",
                recipient_list=[user_email]
            )
        return super(TicketCategoryUpdateView, self).form_valid(form)



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
            "ticket": Ticket.objects.get(pk=self.kwargs["pk"])
        })
        return context

    def form_valid(self, form):
        ticket = Ticket.objects.get(pk=self.kwargs["pk"])
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.save()
        return super(CommentCreateView, self).form_valid(form)

class CommentUpdateView(NotManagerAndLoginRequiredMixin, generic.UpdateView):
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

class CommentDeleteView(NotManagerAndLoginRequiredMixin, generic.DeleteView):
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


