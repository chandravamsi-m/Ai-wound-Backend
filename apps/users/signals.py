from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User
from .utils import log_system_event

@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    if created:
        action = f"System: User created - {instance.email}"
        severity = 'Success'
    else:
        # Check if it was a status change or profile update
        # action = f"System: User records updated - {instance.email}"
        # severity = 'Info'
        # Reduced noise: skip logging for updates
        return
        
    log_system_event(
        user=None, # System level signal
        action=action,
        severity=severity
    )

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    log_system_event(
        user=None,
        action=f"System: User permanently removed - {instance.email}",
        severity='Warning'
    )
