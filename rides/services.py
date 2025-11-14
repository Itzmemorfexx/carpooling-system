from decimal import Decimal
from django.utils import timezone
from .models import Payment, Ride, RideLocation

class PaymentService:
    @staticmethod
    def calculate_fare(ride, number_of_seats):
        """Calculate total fare for a ride request"""
        return ride.price_per_seat * number_of_seats

    @staticmethod
    def split_fare(ride, ride_request):
        """Split fare into payment records"""
        total_fare = ride_request.total_fare
        driver_share = total_fare * Decimal('0.8')  # Driver gets 80%
        platform_share = total_fare * Decimal('0.2')  # Platform gets 20%

        payments = [
            Payment(
                ride_request=ride_request,
                amount=driver_share,
                status='pending',
                payment_method='bank'  # Default to bank transfer for driver
            ),
            Payment(
                ride_request=ride_request,
                amount=platform_share,
                status='pending',
                payment_method='card'  # Platform payment
            )
        ]
        return payments

    @staticmethod
    def process_payment(payment):
        """Process a payment"""
        # In a real application, this would integrate with a payment gateway
        # For now, we'll just mark it as completed
        payment.status = 'completed'
        payment.save()

class LocationService:
    @staticmethod
    def update_ride_location(ride, latitude, longitude):
        """Update the current location of a ride"""
        try:
            location = RideLocation.objects.create(
                ride=ride,
                latitude=latitude,
                longitude=longitude
            )
            return location
        except Exception:
            return None

    @staticmethod
    def get_current_location(ride):
        """Get the most recent location of a ride"""
        try:
            return RideLocation.objects.filter(ride=ride).latest('timestamp')
        except RideLocation.DoesNotExist:
            return None

    @staticmethod
    def get_ride_route(ride):
        """Get the complete route history of a ride"""
        return RideLocation.objects.filter(ride=ride).order_by('timestamp')

    @staticmethod
    def estimate_arrival_time(ride):
        """Estimate arrival time based on current location and route"""
        current_location = LocationService.get_current_location(ride)
        if not current_location:
            return None

        # In a real application, this would use a mapping service
        # to calculate ETA based on current location and destination
        # For now, we'll return a dummy value
        return timezone.now() + timezone.timedelta(minutes=30) 