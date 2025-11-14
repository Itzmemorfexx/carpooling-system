from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('find-ride/', views.find_ride, name='find_ride'),
    path('rides/', views.ride_list, name='ride_list'),
    path('ride/<int:pk>/', views.ride_detail, name='ride_detail'),
    path('ride/new/', views.ride_create, name='ride_create'),
    path('ride/<int:pk>/update/', views.ride_update, name='ride_update'),
    path('ride/<int:pk>/delete/', views.ride_delete, name='ride_delete'),
    path('ride/<int:pk>/book/', views.ride_book, name='ride_book'),
    path('ride/<int:ride_id>/request/<int:request_id>/respond/', views.ride_request_respond, name='ride_request_respond'),
    path('my-rides/', views.my_rides, name='my_rides'),
    path('ride/<int:ride_id>/review/', views.submit_review, name='submit_review'),
    path('user/<int:user_id>/reviews/', views.view_reviews, name='view_reviews'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('ride/<int:pk>/location/update/', views.update_ride_location, name='update_ride_location'),
    path('ride/<int:pk>/location/', views.get_ride_location, name='get_ride_location'),
    path('ride/<int:pk>/track/', views.ride_tracking, name='ride_tracking'),
    path('notifications/', views.notifications, name='notifications'),
    path('api/notifications/unread-count/',views.unread_notification_count, name='unread_notification_count'),
    path('api/notifications/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('ride/request/', views.ride_request, name='ride_request'),
    path('ride/confirm/', views.confirm_ride_request, name='confirm_ride_request'),
    path('ride-request/success/', views.ride_request_success, name='ride_request_success'),
    path('ride-request/<int:request_id>/<str:response>/', views.ride_request_respond, name='ride_request_respond'),
    path('my-rides/passenger/', views.my_passenger_rides, name='my_passenger_rides'), #url for handling user's ride as passenger
    path('ride-request/<int:request_id>/cancel/', views.ride_request_cancel, name='ride_request_cancel'),
] 