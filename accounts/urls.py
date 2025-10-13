from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('<str:username>/', views.profile, name='profile'),
]