from django import forms
from django.contrib.auth.models import User
from .models import Profile, UserPreference
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'profile_picture', 'gender', 'date_of_birth', 
                 'emergency_contact_name', 'emergency_contact_phone', 'preferred_language']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['music_preference', 'smoking_allowed', 'pets_allowed', 'women_only',
                 'max_price_per_km', 'preferred_pickup_time', 'preferred_dropoff_time']
        widgets = {
            'preferred_pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'preferred_dropoff_time': forms.TimeInput(attrs={'type': 'time'}),
        } 
        
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']