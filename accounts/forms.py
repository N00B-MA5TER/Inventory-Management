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
