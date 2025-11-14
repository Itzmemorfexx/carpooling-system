from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from django.utils import timezone
from rides.models import Ride, RideRequest
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    id_document = models.FileField(upload_to='id_documents/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_rating(self):
        """Calculate average rating for the user"""
        from rides.models import RideReview
        reviews = RideReview.objects.filter(reviewee=self.user)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0.0

    def get_total_rides(self):
        """Get total number of rides (as driver and passenger)"""
        rides_as_driver = Ride.objects.filter(driver=self.user).count()
        rides_as_passenger = RideRequest.objects.filter(
            passenger=self.user,
            status__in=['accepted', 'completed']
        ).count()
        return rides_as_driver + rides_as_passenger

    def get_completed_rides(self):
        """Get number of completed rides"""
        rides_as_driver = Ride.objects.filter(
            driver=self.user,
            status='completed'
        ).count()
        rides_as_passenger = RideRequest.objects.filter(
            passenger=self.user,
            status='completed'
        ).count()
        return rides_as_driver + rides_as_passenger

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        # Try to get the profile
        instance.profile.save()
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        Profile.objects.create(user=instance)
    except User.profile.RelatedObjectDoesNotExist:
        # Create profile if the relationship doesn't exist
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    try:
        # Try to get the preferences
        instance.userpreference.save()
    except UserPreference.DoesNotExist:
        # Create preferences if they don't exist
        UserPreference.objects.create(user=instance)
    except User.userpreference.RelatedObjectDoesNotExist:
        # Create preferences if the relationship doesn't exist
        UserPreference.objects.create(user=instance)

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    music_preference = models.BooleanField(default=True)
    smoking_allowed = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    women_only = models.BooleanField(default=False)
    max_price_per_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_pickup_time = models.TimeField(null=True, blank=True)
    preferred_dropoff_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s preferences"

class User(AbstractUser):
    @property
    def unread_notification_count(self):
        return self.notifications.filter(is_read=False).count()
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
        
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='user',
    )