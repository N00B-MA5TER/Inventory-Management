import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Creates (or updates) a superadmin/owner account. Safe to rerun — '
        'also doubles as a way to reset the owner password later, since it '
        'always sets the password and role fresh rather than only on create.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', default='')

    def handle(self, *args, **options):
        password = os.environ.get('OWNER_BOOTSTRAP_PASSWORD')
        if not password:
            raise CommandError('OWNER_BOOTSTRAP_PASSWORD env var must be set.')

        username = options['username']
        email = options['email']

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        if email:
            user.email = email
        user.save()

        user.profile.role = Profile.Role.SUPERADMIN
        user.profile.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} superadmin account "{username}".'))
