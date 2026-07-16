from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Profile

User = get_user_model()


class StaffUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=Profile.Role.choices, label='Role', initial=Profile.Role.ADMIN)

    class Meta:
        model = User
        fields = ['username', 'role']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
        return user


class CustomerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, label='Full Name')
    phone = forms.CharField(max_length=20, label='Phone Number')
    register_as_employee = forms.BooleanField(
        required=False,
        label='I want to register as an employee (needs owner approval)',
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'phone']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.full_name = self.cleaned_data['full_name']
            user.profile.phone = self.cleaned_data['phone']
            user.profile.save()
        return user
