import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Validate FIREBASE_SERVICE_ACCOUNT_PATH resolution and file availability."

    def handle(self, *args, **options):
        configured = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
        resolved = configured if os.path.isabs(configured) else os.path.join(settings.BASE_DIR, configured)

        self.stdout.write(f"Configured path: {configured}")
        self.stdout.write(f"Resolved path:   {resolved}")

        if os.path.exists(resolved):
            self.stdout.write(self.style.SUCCESS("OK: Firebase service-account file exists."))
            return

        self.stdout.write(self.style.ERROR("ERROR: Firebase service-account file not found."))
        self.stdout.write("Fix Backend/.env FIREBASE_SERVICE_ACCOUNT_PATH to an existing JSON file.")
