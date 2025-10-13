from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as auth_logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import LoginForm


def profile(request, username):
    # Placeholder implementation for user profile view
    return render(request, 'accounts/profile.html', {'username': username})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('accounts:profile', username=user.username)
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('core:index')


def register(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile', username=user.username)
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
