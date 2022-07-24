from django.views import generic
from .forms import *
from django.shortcuts import reverse, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class AccountUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "account/account_update.html"
    form_class = AccountModelForm

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(username=user)
        return queryset

    def get_success_url(self):
        return reverse("dashboard:dashboard-chart")






