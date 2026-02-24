from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that uses our custom User model.
    """
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        Self-heals if the local system was reset.
        """
        user_id = validated_token.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # SELF-HEALING: If token is valid but local user is gone (Render restart)
            from core.firestore_service import FirestoreService
            user_data = FirestoreService.get_document('users', user_id)
            if not user_data:
                return None
            
            # Use update_or_create with ID-first lookup to prevent email collisions
            existing_email_user = User.objects.filter(email=user_data['email']).first()
            if existing_email_user and existing_email_user.id != user_id:
                existing_email_user.delete()

            user, created = User.objects.update_or_create(
                id=user_id,
                defaults={
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'status': user_data.get('status', 'ACTIVE'),
                    'isActive': user_data.get('isActive', True),
                    'password': user_data['password']
                }
            )

        # Check if user is still active
        if not user.isActive:
            return None
            
        return user
