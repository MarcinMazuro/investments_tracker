from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    
    # URLs for email verification
    path('account_activation_sent/', views.account_activation_sent, name='account_activation_sent'),
    path('resend_activation_email/', views.resend_activation_email, name='resend_activation_email'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('account_activation_complete/', views.account_activation_complete, name='account_activation_complete'),

    path('<str:username>/', views.profile, name='profile'),
]