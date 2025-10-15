from django.shortcuts import render, redirect
from django.contrib.auth.views import PasswordChangeView, LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from .utils import send_activation_email


def profile(request, username):
    if User.objects.filter(username=username).exists():
        profile_user = User.objects.get(username=username)
        return render(request, 'accounts/profile.html', {'profile_user': profile_user})
    else:
        return render(request, 'core/404.html', status=404)


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
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            login(request, user)
            send_activation_email(request, user)

            # Redirect to the homepage, middleware will handle the rest
            return redirect('core:index') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def account_activation_sent(request):
    if request.user.profile.email_confirmed:
        return redirect('accounts:profile', username=request.user.username)
    return render(request, 'registration/account_activation_sent.html')


@login_required
def resend_activation_email(request):
    user = request.user
    if user.profile.email_confirmed:
        return redirect('core:index')

    send_activation_email(request, user)

    messages.success(request, 'A new activation link has been sent to your email address.')
    return redirect('accounts:account_activation_sent')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.profile.email_confirmed = True
        user.profile.save()
        login(request, user)
        return redirect('accounts:account_activation_complete')
    else:
        return render(request, 'registration/account_activation_invalid.html')


def account_activation_complete(request):
    return render(request, 'registration/account_activation_complete.html')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})  
