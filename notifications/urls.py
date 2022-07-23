from django.urls import path
from .views import *

app_name = "notifications"

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/delete', notification_delete, name='notification-delete'),
    path('delete', notification_delete_all, name='notification-delete-all'),
]