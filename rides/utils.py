from .models import Notification

def create_notification(recipient, sender, ride, message, notification_type):
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        ride=ride,
        message=message,
        notification_type=notification_type
    )