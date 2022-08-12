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
            del self.fields['title']
            del self.fields['project_manager']
            del self.fields["end_date"]




class ManagementTicketCreateModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'deadline',
            'description',
            'tester',
            'status',
            'priority',
            'type',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        id = request.session['project_id']
        project = Project.objects.filter(id=id)
        agents_id = User.objects.filter(role='developer', ticket_flow__in=project).values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        testers = User.objects.filter(role='tester', ticket_flow__in=project)
        statuses = Status.objects.filter(organisation=user.member.organisation)
        priorities = Priority.objects.filter(organisation=user.member.organisation)
        types = Type.objects.filter(organisation=user.member.organisation)
        super(ManagementTicketCreateModelForm, self).__init__(*args, **kwargs)
        self.fields["status"].queryset = statuses
        self.fields["priority"].queryset = priorities
        self.fields["type"].queryset = types
        self.fields['assigned_to'].queryset = members
        self.fields["deadline"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        self.fields["tester"].queryset = testers


class ManagementTicketUpdateModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'deadline',
            'description',
            'tester',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        id = request.session['project_id']
        project = Project.objects.filter(id=id)
        agents_id = User.objects.filter(role='developer', ticket_flow__in=project).values_list('id')
        members = Member.objects.filter(user_id__in=agents_id, organisation=user.member.organisation)
        testers = User.objects.filter(role='tester', ticket_flow__in=project)
        super(ManagementTicketUpdateModelForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = members
        self.fields["deadline"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        self.fields["tester"].queryset = testers


class TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'description',
            'status',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        statuses = Status.objects.filter(organisation=user.member.organisation)
        super(TicketModelForm, self).__init__(*args, **kwargs)
        self.fields["status"].queryset = statuses

class AssignMemberForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.none())

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        id = kwargs.pop("id")
        user = request.user
        project = Project.objects.filter(id=id)
        developer_id = User.objects.filter(role='developer', ticket_flow__in=project).values_list('id')
        members = Member.objects.filter(user_id__in=developer_id, organisation=user.member.organisation)
        super(AssignMemberForm, self).__init__(*args, **kwargs)
        self.fields["member"].queryset = members

class TicketCategoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'status',
            'priority',
            'type',
        )
    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        statuses = Status.objects.filter(organisation=user.member.organisation)
        priorities = Priority.objects.filter(organisation=user.member.organisation)
        types = Type.objects.filter(organisation=user.member.organisation)
        super(TicketCategoryUpdateForm, self).__init__(*args, **kwargs)
        self.fields["status"].queryset = statuses
        self.fields["priority"].queryset = priorities
        self.fields["type"].queryset = types

class CommentModelForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'notes',
            'file',
        )

