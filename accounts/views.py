from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from django.contrib.auth.forms import UserCreationForm

def profile(request, username):
    # Placeholder implementation for user profile view
    return render(request, 'accounts/profile.html', {'username': username})

class CustomLoginView(LoginView):
    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy('accounts:profile', kwargs={'username': username})

def logout(request):
    auth_logout(request)
    return redirect('core:index')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile', username=user.username)
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
