from django.core.management.base import BaseCommand
from users.models import User
from django.contrib.auth.hashers import check_password


class Command(BaseCommand):
    help = 'Debug password verification'

    def handle(self, *args, **options):
        admin = User.objects.filter(email='hardiksharma@gmail.com').first()
        
        if admin:
            self.stdout.write(f"User: {admin.email}")
            self.stdout.write(f"Role: {admin.role}")
            self.stdout.write(f"Active: {admin.isActive}")
            self.stdout.write(f"Password hash (first 30 chars): {admin.password[:30] if admin.password else 'None'}...")
            
            # Test password verification
            test_password = "Admin@123"
            result = admin.verify_password(test_password)
            self.stdout.write(f"\nPassword verification for '{test_password}': {result}")
            
            # Try setting password again and testing
            self.stdout.write("\nSetting password again...")
            admin.set_password(test_password)
            admin.save()
            
            # Test again
            result = admin.verify_password(test_password)
            self.stdout.write(f"Password verification after reset: {result}")
            
            if result:
                self.stdout.write(self.style.SUCCESS("\n✅ Password is working correctly!"))
            else:
                self.stdout.write(self.style.ERROR("\n❌ Password verification still failing!"))
                self.stdout.write("Checking password hash...")
                self.stdout.write(f"Django check_password result: {check_password(test_password, admin.password)}")
        else:
            self.stdout.write(self.style.WARNING("User not found!"))
