from django.urls import path
from .views import *

app_name = 'administration'

urlpatterns = [
    path('', MemberListView.as_view(), name='member-list'),
    path('create/', MemberCreateView.as_view(), name='member-create'),
    path('<int:pk>/', MemberDetailView.as_view(), name='member-detail'),
    path('<int:pk>/update/', MemberUpdateView.as_view(), name='member-update'),
    path('<int:pk>/delete/', MemberDeleteView.as_view(), name='member-delete'),
    path('<int:pk>/request/delete/', MemberRequestDeleteView.as_view(), name='member-request-delete'),
]