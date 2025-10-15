from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy

class EmailVerificationMiddleware:
    """
    Middleware to ensure users have verified their email addresses.
    If a user is authenticated but has not verified their email,
    they are redirected to the 'account_activation_sent' page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_url_names = [
            'accounts:logout',
            'accounts:account_activation_sent',
            'accounts:resend_activation_email',
        ]
        
        # Define URL path prefixes that are always allowed.
        allowed_path_prefixes = [
            '/admin/',
            '/accounts/activate/',
        ]

        if (
            request.user.is_authenticated and
            not request.user.profile.email_confirmed and
            request.path not in [reverse(name) for name in allowed_url_names] and
            not any(request.path.startswith(prefix) for prefix in allowed_path_prefixes)
        ):
            return redirect('accounts:account_activation_sent')
        
        response = self.get_response(request)
        return response
    