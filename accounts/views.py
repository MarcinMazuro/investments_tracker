from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

def profile(request, username):
    # Placeholder implementation for user profile view
    return HttpResponse(f"User profile page for {username}")

class CustomLoginView(LoginView):
    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy('accounts:profile', kwargs={'username': username})
