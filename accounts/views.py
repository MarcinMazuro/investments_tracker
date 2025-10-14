from django.shortcuts import render, redirect
from django.contrib.auth.views import PasswordChangeView, LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as auth_logout, login
from .forms import CustomUserCreationForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.template.loader import render_to_string


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
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until it is confirmed
            user.save()

            # Send activation email
            current_site = get_current_site(request)
            subject = 'Activate Your Account'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(subject, message, 'no-reply@investments_tracker.com', [user.email])

            return redirect('accounts:account_activation_sent')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def account_activation_sent(request):
    return render(request, 'registration/account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'registration/account_activation_complete.html')
    else:
        return render(request, 'registration/account_activation_invalid.html')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'username': self.request.user.username})  
