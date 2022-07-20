from django import forms
from tickets.models import *


class ProjectModelForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
          'title',
          'description',
          'start_date',
          'end_date',
          'project_manager',
          'progress',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        manager_id = User.objects.filter(role='project_manager').values_list('id')
        members = Member.objects.filter(user_id__in=manager_id, organisation=user.account)
        super(ProjectModelForm, self).__init__(*args, **kwargs)
        self.fields['project_manager'].queryset = members



class ManagementTicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'due_to',
            'description',
            'email_disable',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        agents_id = User.objects.filter(role='developer').values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        super(ManagementTicketModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members


class TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'due_to',
            'description',
            'status',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        agents_id = User.objects.filter(role='developer').values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        statuses = Status.objects.filter(organisation=user.member.organisation)
        super(TicketModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members
        self.fields["status"].queryset = statuses

class CommentModelForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'notes',
            'file',
        )

