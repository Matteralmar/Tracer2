from django.urls import path
from .views import *

app_name = "account"

urlpatterns = [
    path('<int:pk>/update/', AccountUpdateView.as_view(), name='account-update'),
]