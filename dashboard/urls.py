from django.urls import path
from .views import *

app_name = "dashboard"

urlpatterns = [
    path('', DashboardChartView.as_view(), name='dashboard-chart'),
    path('project/management/<int:pk>/', ProjectManagementView.as_view(), name='project-management'),
    path('project/management/<int:pk>/assign-member', AssignMemberView.as_view(), name='assign-member'),
    path('project/management/<int:pk>/detail', ManagementTicketDetailView.as_view(), name='management-ticket-detail'),
    path('project/management/create/', ManagementTicketCreateView.as_view(), name='management-ticket-create'),
    path('project/management/<int:pk>/update', ManagementTicketUpdateView.as_view(), name='management-ticket-update'),
    path('project/management/<int:pk>/delete', ManagementTicketDeleteView.as_view(), name='management-ticket-delete'),
    path('project/management/<int:pk>/comment/create', ManagementCommentCreateView.as_view(), name='management-comment-create'),
    path('project/management/<int:pk>/comment/update', ManagementCommentUpdateView.as_view(), name='management-comment-update'),
    path('project/management/<int:pk>/comment/delete', ManagementCommentDeleteView.as_view(), name='management-comment-delete'),
    path('project/test/<int:pk>/', ProjectTestView.as_view(), name='project-test'),
    path('project/test/<int:pk>/update', TestTicketUpdateView.as_view(), name='test-ticket-update'),
    path('project/test/<int:pk>/detail', TestTicketDetailView.as_view(), name='test-ticket-detail'),
    path('project/test/<int:pk>/comment/create', TestCommentCreateView.as_view(), name='test-comment-create'),
    path('project/test/<int:pk>/comment/update', TestCommentUpdateView.as_view(), name='test-comment-update'),
    path('project/test/<int:pk>/comment/delete', TestCommentDeleteView.as_view(), name='test-comment-delete'),
    path('project/create/', ProjectCreateView.as_view(), name='project-create'),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('project/<int:pk>/archive', project_archive, name='project-archive'),
    path('project/<int:pk>/csv', project_tickets_csv, name='project-tickets-csv'),
    path('project/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('project/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),

]