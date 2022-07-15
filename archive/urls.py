from django.urls import path
from .views import *

app_name = "archive"

urlpatterns = [
    path('', ProjectArchiveListView.as_view(), name='archive-project-list'),
    path('project/<int:pk>/detail', ProjectArchiveDetailView.as_view(), name='archive-project-detail'),
    path('project/<int:pk>/unarchive', undo_archive, name='archive-project-unarchive'),
]