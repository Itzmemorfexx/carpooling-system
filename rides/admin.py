from django.contrib import admin
from .models import Ride, RideRequest, RideReview, Payment, Refund, RideLocation, Notification

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('driver', 'pickup_location', 'destination', 'departure_date', 
                   'departure_time', 'available_seats', 'price_per_seat', 'status')
    list_filter = ('status', 'departure_date', 'departure_time')
    search_fields = ('driver__username', 'pickup_location', 'destination')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-departure_date', '-departure_time')

@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ('ride', 'passenger', 'number_of_seats', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ride__driver__username', 'passenger__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(RideReview)
class RideReviewAdmin(admin.ModelAdmin):
    list_display = ('ride', 'reviewer', 'reviewee', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('ride__driver__username', 'reviewer__username', 'reviewee__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('ride_request', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('ride_request__ride__driver__username', 'ride_request__passenger__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'processed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__ride_request__ride__driver__username', 
                    'payment__ride_request__passenger__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(RideLocation)
class RideLocationAdmin(admin.ModelAdmin):
    list_display = ('ride', 'latitude', 'longitude', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('ride__driver__username',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('recipient__username', 'message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'sender', 'ride')
        }),
        ('Notification Details', {
            'fields': ('message', 'notification_type', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )