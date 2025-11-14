from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Ride, RideRequest, RideReview, Notification
from .forms import RideForm, RideRequestForm
from django.contrib.auth.models import User
from django.db.models import Avg
from .services import PaymentService, LocationService
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
import logging
from rides.utils import create_notification
from django.http import JsonResponse, HttpResponseForbidden
from .utils import Notification
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.paginator import Paginator
import logging
import logging
logger = logging.getLogger(__name__)

import logging
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse

from .models import RideRequest, Notification  # adjust import as per your app structure


def ride_list(request):
    """
    View for listing available rides with search functionality.
    """
    rides = Ride.objects.filter(status='active').order_by('departure_date', 'departure_time')
    
    # Get search parameters
    pickup_location = request.GET.get('pickup_location')
    destination = request.GET.get('destination')
    date = request.GET.get('date')
    
    # Apply filters if provided
    if pickup_location:
        rides = rides.filter(pickup_location__icontains=pickup_location)
    if destination:
        rides = rides.filter(destination__icontains=destination)
    if date:
        rides = rides.filter(departure_date=date)
    
    context = {
        'rides': rides,
        'pickup_location': pickup_location,
        'destination': destination,
        'date': date,
    }
    return render(request, 'rides/ride_list.html', context)

@login_required
def ride_create(request):
    if request.method == 'POST':
        form = RideForm(request.POST)
        if form.is_valid():
            ride = form.save(commit=False)
            ride.driver = request.user
            ride.save()
            messages.success(request, 'Your ride has been created!')
            return redirect('ride_detail', pk=ride.pk)
    else:
        form = RideForm()
    return render(request, 'rides/ride_form.html', {'form': form})

def ride_detail(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if request.user.is_authenticated:
        user_request = RideRequest.objects.filter(ride=ride, passenger=request.user).first()
    else:
        user_request = None

    context = {
        'ride': ride,
        'user_request': user_request,
        'requests': ride.requests.filter(status='pending') if request.user == ride.driver else None,
    }
    return render(request, 'rides/ride_detail.html', context)

@login_required
def ride_request(request, pk):
    ride = get_object_or_404(Ride, pk=pk)

    if ride.status != 'active':
        messages.error(request, 'This ride is no longer available for booking.')
        return redirect('ride_detail', pk=pk)

    if request.user == ride.driver:
        messages.error(request, 'You cannot book your own ride.')
        return redirect('ride_detail', pk=pk)

    existing_request = RideRequest.objects.filter(
        ride=ride,
        passenger=request.user,
        status__in=['pending', 'accepted']
    ).first()

    if existing_request:
        messages.error(request, 'You already have a request for this ride.')
        return redirect('ride_detail', pk=pk)

    if request.method == 'POST':
        form = RideRequestForm(request.POST)
        if form.is_valid():
            # Store form data in session
            request.session['ride_request_data'] = {
                'pickup_location': form.cleaned_data['pickup_location'],
                'dropoff_location': form.cleaned_data['dropoff_location'],
                'number_of_seats': form.cleaned_data['number_of_seats'],
                'special_requests': form.cleaned_data.get('special_requests', '')
            }
            request.session['ride_id'] = ride.pk
            return redirect('confirm_ride_request')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = RideRequestForm()

    # Fare preview
    seats = int(request.GET.get('seats', 1))
    total_fare = PaymentService.calculate_fare(ride, seats)
    fare_per_seat = total_fare / seats

    return render(request, 'rides/ride_request_form.html', {
        'form': form,
        'ride': ride,
        'seats': seats,
        'total_fare': total_fare,
        'fare_per_seat': fare_per_seat
    })

from rides.models import Notification, RideRequest, Ride

@login_required
def confirm_ride_request(request):
    # Check if we have the required session data
    ride_id = request.session.get('ride_id')

    # If ride_id is missing, show an error and redirect
    if not ride_id:
        messages.error(request, 'No ride selected. Please select a ride and try again.')
        return redirect('ride_list')  # Redirect to the ride listing page (or any other relevant page)
    
    # Check if ride_request_data exists in session
    if not request.session.get('ride_request_data'):
        messages.error(request, 'Missing ride request data. Please submit your request again.')
        return redirect('ride_list')  # Redirect to the ride listing or another page if necessary
    
    # Fetch the Ride object using the ride_id
    ride = get_object_or_404(Ride, pk=ride_id)

    # Check if the ride has a valid driver
    if not ride.driver:
        messages.error(request, 'This ride does not have a valid driver assigned.')
        return redirect('ride_list')  # Redirect to the ride listing page or any other appropriate action

    # Now proceed with the rest of the logic
    data = request.session['ride_request_data']
    seats = int(data['number_of_seats'])
    total_fare = PaymentService.calculate_fare(ride, seats)

    if request.method == 'POST':
        try:
            # Create and save the ride request
            ride_request = RideRequest(
                ride=ride,
                passenger=request.user,
                pickup_location=data['pickup_location'],
                dropoff_location=data['dropoff_location'],
                number_of_seats=data['number_of_seats'],
                total_fare=Decimal(total_fare),
                special_requests=data.get('special_requests', '')
            )
            ride_request.save()

            # Create notification for the driver (only after confirmation)
            Notification.objects.create(
                recipient=ride.driver,
                sender=request.user,
                ride=ride,
                message=f"{request.user.username} has requested {ride_request.number_of_seats} seat(s) from {ride_request.pickup_location} to {ride_request.dropoff_location}.",
                notification_type='ride_request'
            )

            # Clear session data
            request.session.pop('ride_request_data', None)
            request.session.pop('ride_id', None)

            messages.success(request, 'Your ride request has been submitted successfully!')
            return redirect('ride_request_success')

        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
            return redirect('ride_detail', pk=ride.pk)

    # GET request - show confirmation page
    return render(request, 'rides/confirm_ride_request.html', {
        'data': data,
        'ride': ride,
        'total_fare': total_fare
    })


@login_required
def ride_request_respond(request, request_id, response):
    ride_request = get_object_or_404(RideRequest, id=request_id)

    if ride_request.ride.driver != request.user:
        return HttpResponseForbidden("You are not authorized to respond to this request.")

    if ride_request.status != 'pending':
        messages.error(request, 'This request has already been processed.')
        return redirect('ride_detail', pk=ride_request.ride.pk)

    ride = ride_request.ride

    if response == 'accept':
        # Check if enough seats are available
        if ride.available_seats < ride_request.number_of_seats:
            messages.error(request, f'Not enough available seats. Only {ride.available_seats} seat(s) left.')
            return redirect('ride_detail', pk=ride.pk)

        # Deduct the requested number of seats
        ride.available_seats -= ride_request.number_of_seats
        ride.save()

        ride_request.status = 'accepted'
        notification_type = 'request_accepted'
        message = (
            f'Your request for {ride_request.number_of_seats} seat(s) '
            f'on the ride from {ride.pickup_location} to {ride.destination} has been accepted.'
        )

    elif response == 'reject':
        ride_request.status = 'rejected'
        notification_type = 'request_rejected'
        message = (
            f'Your request for {ride_request.number_of_seats} seat(s) '
            f'on the ride from {ride.pickup_location} to {ride.destination} has been rejected.'
        )

    else:
        messages.error(request, 'Invalid response.')
        return redirect('ride_detail', pk=ride.pk)

    ride_request.save()

    # Create notification for passenger
    Notification.objects.create(
        recipient=ride_request.passenger,
        sender=request.user,
        ride=ride,
        message=message,
        notification_type=notification_type
    )

    messages.success(request, f'Ride request has been {ride_request.status}.')
    return redirect('ride_detail', pk=ride.pk)



def ride_request_success(request):
    return render(request, 'rides/ride_request_success.html')


from django.http import HttpResponseForbidden

@login_required
def ride_request_cancel(request, request_id):
    print("Cookie CSRF:", request.COOKIES.get('csrftoken'))
    print("Form CSRF:", request.POST.get('csrfmiddlewaretoken'))
    if request.method != 'POST':
        return HttpResponseForbidden("You are not authorized to respond to this request.")

    ride_request = get_object_or_404(RideRequest, id=request_id, passenger=request.user)

    if ride_request.status != 'pending':
        messages.warning(request, "Only pending requests can be cancelled.")
        return redirect('my_passenger_rides')

    ride_request.status = 'cancelled'
    ride_request.save()

    Notification.objects.bulk_create([
        Notification(
            recipient=ride_request.ride.driver,
            sender=request.user,
            ride=ride_request.ride,
            message=f'{request.user.username} cancelled their ride request.',
            notification_type='ride_update'
        ),
        Notification(
            recipient=request.user,
            sender=ride_request.ride.driver,
            ride=ride_request.ride,
            message=f'You cancelled your request from {ride_request.ride.pickup_location} to {ride_request.ride.destination}.',
            notification_type='ride_update'
        ),
    ])

    messages.success(request, "Ride request cancelled.")
    return redirect('my_passenger_rides')



    
@login_required
def my_rides(request):
    # Get rides where user is the driver
    rides_as_driver = Ride.objects.filter(driver=request.user)
    
    # Get requests received for user's rides
    received_requests = RideRequest.objects.filter(ride__driver=request.user).exclude(ride__isnull=True)
    
    # Get requests by status
    accepted_requests = received_requests.filter(status='accepted')
    pending_requests = received_requests.filter(status='pending')
    rejected_requests = received_requests.filter(status='rejected')
    cancelled_requests = received_requests.filter(status='cancelled')
    
    # Debug information
    print(f"User: {request.user.username}")
    print(f"Rides as driver: {rides_as_driver.count()}")
    print(f"Total received requests: {received_requests.count()}")
    print(f"Accepted requests: {accepted_requests.count()}")
    print(f"Pending requests: {pending_requests.count()}")
    print(f"Rejected requests: {rejected_requests.count()}")
    print(f"Cancelled requests: {cancelled_requests.count()}")
    
    # Print details of accepted requests
    for req in accepted_requests:
        print(f"Accepted request ID: {req.id}")
        print(f"Ride ID: {req.ride.id}")
        print(f"Passenger: {req.passenger.username}")
        print(f"Status: {req.status}")
        print(f"Total Fare: {req.total_fare}")
        print("---")
    
    # Create a simple context dictionary
    context = {
        'rides_as_driver': rides_as_driver,
        'accepted_requests': accepted_requests,
        'pending_requests': pending_requests,
        'rejected_requests': rejected_requests,
        'cancelled_requests': cancelled_requests,
    }
    return render(request, 'rides/my_rides.html', context)

def home(request):
    """
    View for the welcome homepage.
    """
    return render(request, 'rides/home.html')

def find_ride(request):
    """
    View for the ride search page.
    """
    return render(request, 'rides/find_ride.html')

@login_required
def ride_update(request, pk):
    """
    View for updating an existing ride.
    """
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if the user is the driver of the ride
    if request.user != ride.driver:
        messages.error(request, 'You are not authorized to update this ride.')
        return redirect('ride_detail', pk=pk)
    
    form = RideForm(instance=ride)
    
    if request.method == 'POST':
        form = RideForm(request.POST, instance=ride)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your ride has been updated!')
            return redirect('ride_detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        print("Form errors:", form.errors)
        messages.error(request, 'Please correct the errors below.')
        
    
    return render(request, 'rides/ride_form.html', {'form': form, 'ride': ride})

@login_required
def ride_delete(request, pk):
    """
    View for deleting a ride.
    """
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if the user is the driver of the ride
    if request.user != ride.driver:
        messages.error(request, 'You are not authorized to delete this ride.')
        return redirect('ride_detail', pk=pk)
    
    if request.method == 'POST':
        ride.delete()
        messages.success(request, 'Your ride has been deleted!')
        return redirect('my_rides')
    
    return render(request, 'rides/ride_confirm_delete.html', {'ride': ride})

@login_required
def ride_book(request, pk):
    """
    View for booking a ride.
    """
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if the ride is active
    if ride.status != 'active':
        messages.error(request, 'This ride is no longer available for booking.')
        return redirect('ride_detail', pk=pk)
    
    # Check if user is the driver
    if request.user == ride.driver:
        messages.error(request, 'You cannot book your own ride.')
        return redirect('ride_detail', pk=pk)
    
    # Check if user already has a pending request
    existing_request = RideRequest.objects.filter(
        ride=ride,
        passenger=request.user,
        status__in=['pending', 'accepted']
    ).first()
    
    if existing_request:
        messages.error(request, 'You already have a request for this ride.')
        return redirect('ride_detail', pk=pk)
    
    if request.method == 'POST':
        form = RideRequestForm(request.POST)
        if form.is_valid():
            ride_request = form.save(commit=False)
            ride_request.ride = ride
            ride_request.passenger = request.user
            ride_request.save()
            messages.success(request, 'Your ride request has been submitted!')
            return redirect('ride_detail', pk=pk)
    else:
        form = RideRequestForm()
    
    return render(request, 'rides/ride_request_form.html', {
        'form': form,
        'ride': ride
    })

@login_required
def submit_review(request, ride_id):
    """Submit a review for a ride"""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is involved in the ride
    if not (ride.driver == request.user or 
            ride.requests.filter(passenger=request.user, status='accepted').exists()):
        messages.error(request, 'You can only review rides you were involved in.')
        return redirect('ride_detail', pk=ride_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        reviewee_id = request.POST.get('reviewee')
        
        try:
            reviewee = User.objects.get(id=reviewee_id)
            
            # Create review
            review = RideReview.objects.create(
                ride=ride,
                reviewer=request.user,
                reviewee=reviewee,
                rating=rating,
                comment=comment
            )
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('ride_detail', pk=ride_id)
            
        except User.DoesNotExist:
            messages.error(request, 'Invalid user selected.')
    
    # Get users to review (excluding self)
    users_to_review = []
    if ride.driver != request.user:
        users_to_review.append(ride.driver)
    for request_obj in ride.requests.filter(status='accepted'):
        if request_obj.passenger != request.user:
            users_to_review.append(request_obj.passenger)
    
    context = {
        'ride': ride,
        'users_to_review': users_to_review,
    }
    return render(request, 'rides/submit_review.html', context)

@login_required
def view_reviews(request, user_id):
    """View all reviews for a user"""
    user = get_object_or_404(User, id=user_id)
    reviews = RideReview.objects.filter(reviewee=user).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'user': user,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'rides/view_reviews.html', context)

@login_required
def my_reviews(request):
    """View all reviews given and received by the user"""
    reviews_given = RideReview.objects.filter(reviewer=request.user).order_by('-created_at')
    reviews_received = RideReview.objects.filter(reviewee=request.user).order_by('-created_at')
    
    context = {
        'reviews_given': reviews_given,
        'reviews_received': reviews_received,
    }
    return render(request, 'rides/my_reviews.html', context)

@login_required
def update_ride_location(request, pk):
    """Update the current location of a ride"""
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if user is the driver
    if request.user != ride.driver:
        messages.error(request, 'Only the driver can update the ride location.')
        return redirect('ride_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            latitude = float(request.POST.get('latitude'))
            longitude = float(request.POST.get('longitude'))
            
            location = LocationService.update_ride_location(ride, latitude, longitude)
            
            if location:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Location updated successfully',
                    'timestamp': location.timestamp.isoformat()
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to update location'
                }, status=400)
                
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid coordinates'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@login_required
def ride_tracking(request, pk):
    """View for tracking a ride in real-time"""
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if user is involved in the ride
    if not (ride.driver == request.user or 
            ride.requests.filter(passenger=request.user, status='accepted').exists()):
        messages.error(request, 'You can only track rides you are involved in.')
        return redirect('ride_detail', pk=pk)
    
    # Get current location and route history
    current_location = LocationService.get_current_location(ride)
    route_history = LocationService.get_ride_route(ride)
    
    # Get estimated arrival time
    estimated_arrival = LocationService.estimate_arrival_time(ride)
    
    context = {
        'ride': ride,
        'current_location': current_location,
        'route_history': route_history,
        'estimated_arrival': estimated_arrival,
    }
    return render(request, 'rides/ride_tracking.html', context)

@login_required
def get_ride_location(request, pk):
    """API endpoint to get current ride location"""
    ride = get_object_or_404(Ride, pk=pk)
    
    # Check if user is involved in the ride
    if not (ride.driver == request.user or 
            ride.requests.filter(passenger=request.user, status='accepted').exists()):
        return JsonResponse({
            'status': 'error',
            'message': 'Unauthorized'
        }, status=403)
    
    current_location = LocationService.get_current_location(ride)
    
    if current_location:
        return JsonResponse({
            'status': 'success',
            'latitude': float(current_location.latitude),
            'longitude': float(current_location.longitude),
            'timestamp': current_location.timestamp.isoformat()
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'No location data available'
        }, status=404)

#view for listing notifications
@login_required
def notifications(request):
    """View all notifications"""
    notifications = request.user.notifications.all()
    return render(request, 'notifications/notifications.html', {'notifications': notifications})
    
   
def profile(request):
    user_rides = Ride.objects.filter(driver=request.user)
    print("Fetched rides:", user_rides)
    
    return render(request, 'users/profile.html', {
        'user_rides_as_driver' : user_rides
    })

User = get_user_model()


import logging
logger = logging.getLogger(__name__)

def create_notification(recipient, sender, ride, message, notification_type):
    try:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            ride=ride,
            message=message,
            notification_type=notification_type
        )
        logger.info(f"Notification created for {recipient} with message: {message}")
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")

@login_required
def confirm_ride_request(request):
    # Check if we have the required session data
    ride_id = request.session.get('ride_id')

    # If ride_id is missing, show an error and redirect
    if not ride_id:
        messages.error(request, 'No ride selected. Please select a ride and try again.')
        return redirect('ride_list')  # Redirect to the ride listing page (or any other relevant page)
    
    # Check if ride_request_data exists in session
    if not request.session.get('ride_request_data'):
        messages.error(request, 'Missing ride request data. Please submit your request again.')
        return redirect('ride_list')  # Redirect to the ride listing or another page if necessary
    
    # Fetch the Ride object using the ride_id
    ride = get_object_or_404(Ride, pk=ride_id)

    # Check if the ride has a valid driver
    if not ride.driver:
        messages.error(request, 'This ride does not have a valid driver assigned.')
        return redirect('ride_list')  # Redirect to the ride listing page or any other appropriate action

    # Now proceed with the rest of the logic
    data = request.session['ride_request_data']
    seats = int(data['number_of_seats'])
    total_fare = PaymentService.calculate_fare(ride, seats)

    if request.method == 'POST':
        try:
            # Create and save the ride request
            ride_request = RideRequest(
                ride=ride,
                passenger=request.user,
                pickup_location=data['pickup_location'],
                dropoff_location=data['dropoff_location'],
                number_of_seats=data['number_of_seats'],
                total_fare=Decimal(total_fare),
                special_requests=data.get('special_requests', '')
            )
            ride_request.save()

            # Create notification for the driver (only after confirmation)
            try:
                print(f"Attempting to create notification for driver: {ride.driver}, active: {getattr(ride.driver, 'is_active', 'Unknown')}")
                if getattr(ride.driver, 'is_active', True):
                    Notification.objects.create(
                        recipient=ride.driver,
                        sender=request.user,
                        ride=ride,
                        message=f"{request.user.username} has requested {ride_request.number_of_seats} seat(s) from {ride_request.pickup_location} to {ride_request.dropoff_location}.",
                        notification_type='ride_request'
                    )
                    logger.info(f"Notification created for driver {ride.driver} for ride request by {request.user.username}")
                    print("Notification created successfully.")
                else:
                    print("Driver is not active. Notification not created.")
            except Exception as e:
                logger.error(f"Failed to create notification in confirm_ride_request: {e}")
                print(f"Exception during notification creation: {e}")

            # Clear session data
            request.session.pop('ride_request_data', None)
            request.session.pop('ride_id', None)

            messages.success(request, 'Your ride request has been submitted successfully!')
            return redirect('ride_request_success')

        except Exception as e:
            logger.error(f"Error submitting ride request: {e}")
            messages.error(request, f'Error submitting request: {str(e)}')
            return redirect('ride_detail', pk=ride.pk)

    # GET request - show confirmation page
    return render(request, 'rides/confirm_ride_request.html', {
        'data': data,
        'ride': ride,
        'total_fare': total_fare
    })
    
def unread_notification_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@require_POST
@login_required
def mark_notification_as_read(request ):
    notification_id = request.POST.get('notification_id')
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': 'True', 'message': 'Notifications marked as read.'})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
    
#view for handling users's ride as passenger
@login_required
def  my_passenger_rides(request):
    print("Cookie CSRF:", request.COOKIES.get('csrftoken'))
    print("Form CSRF:", request.POST.get('csrfmiddlewaretoken'))
    requests = RideRequest.objects.filter(passenger=request.user).order_by('-created_at')
    paginator = Paginator(requests, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'rides/my_passengers_ride.html', {'page_obj': page_obj})
    
    




