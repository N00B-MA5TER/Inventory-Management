from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

from accounts.decorators import superadmin_required
from accounts.forms import StaffUserCreationForm
from accounts.models import ActionLog

User = get_user_model()


@superadmin_required
def user_list(request):
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})


@superadmin_required
def user_create(request):
    if request.method == 'POST':
        form = StaffUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ActionLog.objects.create(
                user=request.user,
                action=f'Created account "{user.username}" with role {user.profile.get_role_display()}',
            )
            messages.success(request, f'Account "{user.username}" was created.')
            return redirect('accounts:user_list')
    else:
        form = StaffUserCreationForm()

    return render(request, 'accounts/user_form.html', {'form': form})
