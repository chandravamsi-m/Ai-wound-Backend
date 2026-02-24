from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'List all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        
        self.stdout.write(f"\nTotal users: {users.count()}\n")
        self.stdout.write("-" * 80)
        
        for user in users:
            self.stdout.write(f"\nID: {user.id}")
            self.stdout.write(f"Name: {user.name}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Role: {user.role}")
            self.stdout.write(f"Status: {user.status}")
            self.stdout.write(f"Active: {user.isActive}")
            self.stdout.write(f"Has Password: {bool(user.password)}")
            self.stdout.write("-" * 80)
