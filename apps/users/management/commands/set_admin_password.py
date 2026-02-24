from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Set admin password for testing'

    def handle(self, *args, **options):
        admin = User.objects.filter(role='Admin').first()
        
        if admin:
            self.stdout.write(f"Admin user found: {admin.email}")
            admin.set_password("Admin@123")
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Password set for {admin.email}'))
            
            # Verify
            if admin.verify_password("Admin@123"):
                self.stdout.write(self.style.SUCCESS('✅ Password verification successful!'))
        else:
            self.stdout.write(self.style.WARNING('No admin user found, creating one...'))
            admin = User.objects.create(
                name="System Administrator",
                email="admin@hospital.com",
                role="Admin",
                status="ACTIVE",
                isActive=True
            )
            admin.set_password("Admin@123")
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user created: {admin.email}'))
