from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import superadmin_required
from accounts.forms import CustomerRegistrationForm, StaffUserCreationForm
from accounts.models import ActionLog, Profile, RoleUpgradeRequest

User = get_user_model()


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'accounts/landing.html')

    if request.user.profile.is_customer:
        return redirect('billing:order_build')
    return redirect('inventory:product_list')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data['register_as_employee']:
                RoleUpgradeRequest.objects.create(user=user)
                messages.success(
                    request,
                    'Account created! Your employee request is waiting for the owner\'s approval. '
                    'You can use the site as a customer in the meantime.',
                )
            else:
                messages.success(request, 'Account created! Welcome.')
            login(request, user)
            return redirect('home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


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


@superadmin_required
def role_request_queue(request):
    pending = RoleUpgradeRequest.objects.filter(
        status=RoleUpgradeRequest.Status.PENDING
    ).select_related('user__profile')
    history = RoleUpgradeRequest.objects.exclude(
        status=RoleUpgradeRequest.Status.PENDING
    ).select_related('user__profile', 'reviewed_by')[:20]

    return render(request, 'accounts/role_request_queue.html', {'pending': pending, 'history': history})


@superadmin_required
def role_request_approve(request, pk):
    role_request = get_object_or_404(RoleUpgradeRequest, pk=pk, status=RoleUpgradeRequest.Status.PENDING)
    if request.method == 'POST':
        role_request.user.profile.role = Profile.Role.ADMIN
        role_request.user.profile.save()
        role_request.status = RoleUpgradeRequest.Status.APPROVED
        role_request.reviewed_by = request.user
        role_request.reviewed_at = timezone.now()
        role_request.save()

        ActionLog.objects.create(
            user=request.user,
            action=f'Approved employee request for "{role_request.user.username}"',
        )
        messages.success(request, f'"{role_request.user.username}" is now an employee.')

    return redirect('accounts:role_request_queue')


@superadmin_required
def role_request_reject(request, pk):
    role_request = get_object_or_404(RoleUpgradeRequest, pk=pk, status=RoleUpgradeRequest.Status.PENDING)
    if request.method == 'POST':
        role_request.status = RoleUpgradeRequest.Status.REJECTED
        role_request.reviewed_by = request.user
        role_request.reviewed_at = timezone.now()
        role_request.save()

        ActionLog.objects.create(
            user=request.user,
            action=f'Rejected employee request for "{role_request.user.username}"',
        )
        messages.success(request, f'Request from "{role_request.user.username}" was rejected.')

    return redirect('accounts:role_request_queue')
