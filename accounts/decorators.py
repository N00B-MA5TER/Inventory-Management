from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def superadmin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_superadmin:
            messages.error(request, 'Only the owner account can do that.')
            return redirect('inventory:product_list')
        return view_func(request, *args, **kwargs)

    return wrapper
