from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import ProfileUpdateForm, UserPreferenceForm, CustomUserCreationForm
from .models import Profile, UserPreference
from django.core.mail import send_mail
from django.conf import settings
from rides.models import Ride, RideRequest
import random
import string
from django.contrib.auth.models import User

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

@login_required
def profile(request, username=None):
    """View user profile with all related data"""
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    # Get or create profile if it doesn't exist
    try:
        profile = Profile.objects.get(user=profile_user)
    except Profile.DoesNotExist:
        profile = None
    
    # Get user preferences (handle case where it doesn't exist)
    try:
        preferences = request.user.userpreference
    except AttributeError:
        preferences = None
    
    # Get ride data
    user_rides_as_driver = Ride.objects.filter(driver=request.user)
    user_rides_as_passenger = RideRequest.objects.filter(passenger=request.user).select_related('ride')
    
    print(f"Debug: {user_rides_as_driver.count()} driver rides, {user_rides_as_passenger.count()} passenger rides")
    
    context = {
        'profile': profile,
        'profile_user': profile_user,
        'preferences': preferences,
        'rating': profile.get_rating(),
        'total_rides': profile.get_total_rides(),
        'user_rides_as_driver': user_rides_as_driver,
        'user_rides_as_passenger': user_rides_as_passenger,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def profile_update(request):
    """Update user profile"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'users/profile_update.html', {'form': form})

@login_required
def preferences_update(request):
    """Update user preferences"""
    #Get or create user preferences
    user_preference, created = UserPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=user_preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated!')
            return redirect('profile')
    else:
        form = UserPreferenceForm(instance=user_preference)
    return render(request, 'users/preferences_update.html', {'form': form})

@login_required
def verify_phone(request):
    """Send phone verification code"""
    if request.method == 'POST':
        verification_code = generate_verification_code()
        # In a real application, you would send this code via SMS
        # For development, we'll just store it in the session
        request.session['phone_verification_code'] = verification_code
        messages.success(request, 'Verification code sent to your phone!')
        return redirect('verify_phone_confirm')
    return render(request, 'users/verify_phone.html')

@login_required
def verify_phone_confirm(request):
    """Confirm phone verification code"""
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        stored_code = request.session.get('phone_verification_code')
        if code == stored_code:
            request.user.profile.is_phone_verified = True
            request.user.profile.save()
            messages.success(request, 'Phone number verified successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Invalid verification code!')
    return render(request, 'users/verify_phone_confirm.html')

@login_required
def verify_email(request):
    """Send email verification link"""
    if not request.user.profile.is_email_verified:
        verification_code = generate_verification_code()
        request.session['email_verification_code'] = verification_code
        
        # Send verification email
        verification_link = f"{settings.SITE_URL}/users/verify-email-confirm/{verification_code}/"
        send_mail(
            'Verify your email address',
            f'Click the following link to verify your email: {verification_link}',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        messages.success(request, 'Verification email sent!')
    return redirect('profile')

@login_required
def verify_email_confirm(request, code):
    """Confirm email verification"""
    stored_code = request.session.get('email_verification_code')
    if code == stored_code:
        request.user.profile.is_email_verified = True
        request.user.profile.save()
        messages.success(request, 'Email verified successfully!')
    else:
        messages.error(request, 'Invalid verification code!')
    return redirect('profile')

@login_required
def upload_id(request):
    """Upload ID document for verification"""
    if request.method == 'POST' and request.FILES.get('id_document'):
        profile = request.user.profile
        profile.id_document = request.FILES['id_document']
        profile.verification_status = 'pending'
        profile.save()
        messages.success(request, 'ID document uploaded successfully!')
        return redirect('profile')
    return render(request, 'users/upload_id.html')


#view for managing ride request
@login_required
def manage_ride_request(request, request_id):
    ride_request = get_object_or_404(RideRequest, id=request_id, ride__driver=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action =='accept':
            ride_request.status = 'accepted'
            ride_request.save()
            messages.success(request, 'request accepted successfully')
            return redirect('pending_requests')
        elif action == 'reject':
            ride_request.status = 'rejected'
            ride_request.save()
            messages.success(request, 'Request rejected')
            return redirect('pending_requests')
        
    #getting passenger details
    passenger = ride_request.passenger
    passenger_profile = passenger.profile
    
    context = {
        'ride_request': ride_request,
        'passenger': passenger,
        'passenger_profile': passenger_profile,
        'ride': ride_request.ride,
    }
    
    return render(request, 'rides/manage_request.html', context)


# view for handling pending requests
@login_required
def pending_requests(request):
    requests = RideRequest.objects.filter(ride__driver=request.user, status='pending')
    return render(request, 'rides/my_rides.html', {'requests': requests})