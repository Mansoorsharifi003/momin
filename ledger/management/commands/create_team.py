from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create 1 superuser (if none exists) and 3 staff users'

    def handle(self, *args, **options):
        # Superuser — only if you don't already have one
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('owner', 'owner@momin.com', 'owner123')
            self.stdout.write(self.style.SUCCESS('Superuser "owner" created (password: owner123)'))
        else:
            self.stdout.write('A superuser already exists — keeping it.')

        # Staff users (can use the app, but NOT Tools / admin)
        for i in (1, 2, 3):
            uname = f'staff{i}'
            if not User.objects.filter(username=uname).exists():
                User.objects.create_user(uname, password=f'staff{i}123', is_staff=False)
                self.stdout.write(self.style.SUCCESS(f'Staff "{uname}" created (password: staff{i}123)'))
        self.stdout.write(self.style.SUCCESS('Done.'))