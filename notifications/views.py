from django.shortcuts import render
from django.views import generic
from .models import *
from administration.mixins import *
from django.contrib.auth.mixins import LoginRequiredMixin


class NotificationListView(LoginRequiredMixin, generic.ListView):
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user).order_by('-created_date')
        return queryset

def notification_delete(request, pk):
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    notification = Notification.objects.get(id=pk, recipient=user)
    notification.delete()
    return redirect('/notifications/')

def notification_delete_all(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('/login/')
    notifications = Notification.objects.filter(recipient=user)
    notifications.delete()
    return redirect('/notifications/')