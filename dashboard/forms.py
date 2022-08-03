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
        id = request.session['project_id']
        project = Project.objects.filter(id=id)
        agents_id = User.objects.filter(role='developer', ticket_flow__in=project).values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        super(ManagementTicketModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members
        self.fields["due_to"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))


class TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'due_to',
            'description',
            'status',
            'tester',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        statuses = Status.objects.filter(organisation=user.member.organisation)
        tester = User.objects.filter(username=user.username)
        super(TicketModelForm, self).__init__(*args, **kwargs)
        self.fields["due_to"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        self.fields["status"].queryset = statuses
        self.fields["tester"].queryset = tester

class AssignMemberForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.none())

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        id = kwargs.pop("id")
        user = request.user
        project_id = Ticket.objects.filter(id=id).values_list('project_id', flat=True)[0]
        project = Project.objects.filter(id=project_id)
        developer_id = User.objects.filter(role='developer', ticket_flow__in=project).values_list('id')
        members = Member.objects.filter(user_id__in=developer_id, organisation=user.member.organisation)
        super(AssignMemberForm, self).__init__(*args, **kwargs)
        self.fields["member"].queryset = members

class CommentModelForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'notes',
            'file',
        )

