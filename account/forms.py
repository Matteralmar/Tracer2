from django import forms
from tickets.models import *


class AccountModelForm(forms.ModelForm):
    class Meta:
      model = User
      fields = (
          'username',
          'first_name',
          'last_name',
      )

