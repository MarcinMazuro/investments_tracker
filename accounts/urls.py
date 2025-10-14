from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('<str:username>/', views.profile, name='profile'),
]