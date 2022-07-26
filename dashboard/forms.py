from django import forms
from tickets.models import *
from datetime import datetime

class ProjectModelForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
          'title',
          'description',
          'end_date',
          'project_manager',
          'progress',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        super(ProjectModelForm, self).__init__(*args, **kwargs)
        if user.is_organizer:
            manager_id = User.objects.filter(role='project_manager').values_list('id')
            members = Member.objects.filter(user_id__in=manager_id, organisation=user.account)
            self.fields['project_manager'].queryset = members
            self.fields["end_date"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        else:
            del self.fields['project_manager']
            self.fields["end_date"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))




class ManagementTicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'due_to',
            'description',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        agents_id = User.objects.filter(role='developer').values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        super(ManagementTicketModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members
        self.fields["due_to"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))


class TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'due_to',
            'description',
            'status',
            'tester',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        agents_id = User.objects.filter(role='developer').values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        statuses = Status.objects.filter(organisation=user.member.organisation)
        tester = User.objects.filter(username=user.username)
        super(TicketModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members
        self.fields["due_to"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        self.fields["status"].queryset = statuses
        self.fields["tester"].queryset = tester

class CommentModelForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'notes',
            'file',
        )

