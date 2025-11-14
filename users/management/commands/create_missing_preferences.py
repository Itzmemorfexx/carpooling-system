from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserPreference

class Command(BaseCommand):
    help = 'Creates missing user preferences'

    def handle(self, *args, **kwargs):
        users_without_preferences = []
        for user in User.objects.all():
            try:
                # Try to access the preferences
                user.userpreference
            except User.userpreference.RelatedObjectDoesNotExist:
                # Create preferences if they don't exist
                UserPreference.objects.create(user=user)
                users_without_preferences.append(user.username)
        
        if users_without_preferences:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created preferences for users: {", ".join(users_without_preferences)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('All users already have preferences')
            ) 