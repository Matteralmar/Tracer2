from django.urls import path
from .views import *

app_name = "tickets"

urlpatterns = [
    path('', TicketListView.as_view(), name='ticket-list'),
    path('json/', TicketJsonView.as_view(), name='ticket-list-json'),
    path('create/', TicketCreateView.as_view(), name='ticket-create'),
    path('type/', TypeListView.as_view(), name='type-list'),
    path('type/<int:pk>/', TypeDetailView.as_view(), name='type-detail'),
    path('type-create/', TypeCreateView.as_view(), name='type-create'),
    path('type/<int:pk>/update/', TypeUpdateView.as_view(), name='type-update'),
    path('type/<int:pk>/delete/', TypeDeleteView.as_view(), name='type-delete'),
    path('priority/', PriorityListView.as_view(), name='priority-list'),
    path('priority/<int:pk>/', PriorityDetailView.as_view(), name='priority-detail'),
    path('priority-create/', PriorityCreateView.as_view(), name='priority-create'),
    path('priority/<int:pk>/update/', PriorityUpdateView.as_view(), name='priority-update'),
    path('priority/<int:pk>/delete/', PriorityDeleteView.as_view(), name='priority-delete'),
    path('status/', StatusListView.as_view(), name='status-list'),
    path('status/<int:pk>/', StatusDetailView.as_view(), name='status-detail'),
    path('status-create/', StatusCreateView.as_view(), name='status-create'),
    path('status/<int:pk>/update/', StatusUpdateView.as_view(), name='status-update'),
    path('status/<int:pk>/delete/', StatusDeleteView.as_view(), name='status-delete'),
    path('comments/<int:pk>/', CommentCreateView.as_view(), name='ticket-comment-create'),
    path('comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='ticket-comment-delete'),
    path('<int:pk>/comments/update/', CommentUpdateView.as_view(), name='ticket-comment-update'),
    path('<int:pk>/category/', TicketCategoryUpdateView.as_view(), name='ticket-status-update'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('<int:pk>/update/', TicketUpdateView.as_view(), name='ticket-update'),
    path('<int:pk>/delete/', TicketDeleteView.as_view(), name='ticket-delete'),
    path('<int:pk>/request/change/', TicketRequestChangeView.as_view(), name='ticket-request-change'),
    path('filter/', filter_, name='ticket-filter'),
]
