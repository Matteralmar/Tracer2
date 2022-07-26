from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect


def already_logged(function):
    def _function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/dashboard')
        return function(request, *args, **kwargs)
    return _function