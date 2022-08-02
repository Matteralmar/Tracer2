from django import forms
from tickets.models import *
from django.db.models import Q



class MemberModelForm(forms.ModelForm):

    class Meta:
      model = User
      fields = (
          'username',
          'first_name',
          'last_name',
          'email',
          'role',
          'ticket_flow'
      )
    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        user = request.user
        super(MemberModelForm, self).__init__(*args, **kwargs)
        if user.is_organizer:
            projects = Project.objects.filter(organisation=user.account, archive=False)
        else:
            projects = Project.objects.filter(organisation=user.member.organisation, project_manager__user=user, archive=False)
            self.fields['role'].choices = (
                ('tester', 'Tester'),
                ('developer', 'Developer'),
            )
        self.fields["ticket_flow"].queryset = projects
