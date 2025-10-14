from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import PasswordChangeView, LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as auth_logout, login
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


def profile(request, username):
    # Placeholder implementation for user profile view
    return render(request, 'accounts/profile.html', {'username': username})


# def user_login(request):
#     if request.user.is_authenticated:
#         return redirect('core:index')
    
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return redirect('accounts:profile', username=user.username)
#             else:
#                 form.add_error(None, 'Invalid username or password')
#     else:
#         form = LoginForm()
#     return render(request, 'accounts/login.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})



def logout(request):
    auth_logout(request)
    return render(request, 'accounts/logout.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile', username=user.username)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})  
