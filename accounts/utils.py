from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def send_activation_email(request, user):
    """
    Generates and sends an account activation email to the given user.
    """
    current_site = get_current_site(request)
    subject = 'Activate Your Account'
    message = render_to_string('registration/account_activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    send_mail(subject, message, 'no-reply@investments_tracker.com', [user.email])
    