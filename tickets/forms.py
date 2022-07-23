from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class TicketModelForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'assigned_to',
            'project',
            'due_to',
            'description',
        )
    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        developer_id = User.objects.filter(role='developer').values_list('id')
        archived = False
        if user.is_organizer:
            members = Member.objects.filter(user_id__in=developer_id, organisation=user.account)
            projects = Project.objects.filter(organisation=user.account, archive=archived)
        elif user.role == 'tester':
            members = Member.objects.filter(user_id__in=developer_id, organisation=user.member.organisation)
            projects = Project.objects.filter(organisation=user.member.organisation, title=user.ticket_flow, archive=archived)
        else:
            members = Member.objects.filter(user=user, organisation=user.member.organisation)
            projects = Project.objects.filter(organisation=user.member.organisation, title=user.ticket_flow, archive=archived)
        super(TicketModelForm, self).__init__(*args, **kwargs)
        self.fields["due_to"] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.now().date()}))
        self.fields["assigned_to"].queryset = members
        self.fields["project"].queryset = projects

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
        )
        field_classes = {'username': UsernameField}

class AssignMemberForm(forms.Form):
    member = forms.ModelChoiceField(queryset=Member.objects.none())

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        developer_id = User.objects.filter(role='developer').values_list('id')
        members = Member.objects.filter(user_id__in=developer_id, organisation=user.account)
        super(AssignMemberForm, self).__init__(*args, **kwargs)
        self.fields["member"].queryset = members

class TicketSatusUpdateForm(forms.ModelForm):
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
        if user.is_organizer:
            statuses = Status.objects.filter(organisation=user.account)
            priorities = Priority.objects.filter(organisation=user.account)
            types = Type.objects.filter(organisation=user.account)
        else:
            statuses = Status.objects.filter(organisation=user.member.organisation)
            priorities = Priority.objects.filter(organisation=user.member.organisation)
            types = Type.objects.filter(organisation=user.member.organisation)
        super(TicketSatusUpdateForm, self).__init__(*args, **kwargs)
        self.fields["status"].queryset = statuses
        self.fields["priority"].queryset = priorities
        self.fields["type"].queryset = types

class StatusModelForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = (
            'name',
            'test_status',
        )

class PriorityModelForm(forms.ModelForm):
    class Meta:
        model = Priority
        fields = (
            'name',
        )

class TypeModelForm(forms.ModelForm):
    class Meta:
        model = Type
        fields = (
            'name',
        )

class CommentModelForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'notes',
            'file',
        )