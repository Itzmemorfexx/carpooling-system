from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/preferences/', views.preferences_update, name='preferences_update'),
    path('profile/verify-phone/', views.verify_phone, name='verify_phone'),
    path('profile/verify-phone/confirm/', views.verify_phone_confirm, name='verify_phone_confirm'),
    path('profile/verify-email/', views.verify_email, name='verify_email'),
    path('profile/verify-email/confirm/<str:code>/', views.verify_email_confirm, name='verify_email_confirm'),
    path('profile/upload-id/', views.upload_id, name='upload_id'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    #url for managing ride request
    path('requests/manage/<int:request_id>/', views.manage_ride_request, name='manage_ride_request'),
    # View other profiles
    path('profile/<str:username>/', views.profile, name='user_profile'),
    #url for getting pending requests
    path('requests/pending/', views.pending_requests, name='pending_requests'),
] 