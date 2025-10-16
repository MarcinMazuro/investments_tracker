from unittest.mock import patch
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.core import mail
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .forms import CustomUserCreationForm
from .middleware import EmailVerificationMiddleware
from .models import Profile
from .utils import send_activation_email

User = get_user_model()


class ProfileModelTests(TestCase):
    def test_profile_created_with_user(self):
        user = User.objects.create_user('alice', 'alice@example.com', 'StrongPass123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertFalse(user.profile.email_confirmed)

    def test_profile_remains_on_user_update(self):
        user = User.objects.create_user('bob', 'bob@example.com', 'StrongPass123')
        user.first_name = 'Robert'
        user.save()
        self.assertTrue(Profile.objects.filter(user=user).exists())


class CustomUserCreationFormTests(TestCase):
    def test_form_accepts_valid_payload(self):
        form = CustomUserCreationForm(data={
            'username': 'charlie',
            'email': 'charlie@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        self.assertTrue(form.is_valid())

    def test_form_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user('dana', 'duplicate@example.com', 'StrongPass123')
        form = CustomUserCreationForm(data={
            'username': 'duplicate',
            'email': 'Duplicate@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.confirmed_user = User.objects.create_user('eve', 'eve@example.com', 'StrongPass123')
        self.confirmed_user.profile.email_confirmed = True
        self.confirmed_user.profile.save()
        self.unconfirmed_user = User.objects.create_user('frank', 'frank@example.com', 'StrongPass123')

    def test_profile_view_displays_existing_user(self):
        response = self.client.get(reverse('accounts:profile', kwargs={'username': self.confirmed_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertEqual(response.context['profile_user'], self.confirmed_user)

    def test_profile_view_returns_404_for_missing_user(self):
        response = self.client.get(reverse('accounts:profile', kwargs={'username': 'missing'}))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_register_view_get_renders_form(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    @patch('accounts.views.send_activation_email')
    def test_register_view_creates_user_and_logs_in(self, mock_send):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'george',
            'email': 'george@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('core:index'))
        new_user = User.objects.get(username='george')
        self.assertTrue(self.client.get(reverse('accounts:account_activation_sent')).status_code, 200)
        self.assertFalse(new_user.profile.email_confirmed)
        mock_send.assert_called_once_with(response.wsgi_request, new_user)

    def test_register_view_rejects_invalid_payload(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': '',
            'email': 'invalid',
            'password1': 'short',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='invalid').exists())

    def test_register_view_redirects_authenticated_user(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('core:index'))

    def test_login_view_redirects_authenticated_get(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accounts:profile', kwargs={'username': 'eve'}))

    def test_login_view_successful_post(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'eve',
            'password': 'StrongPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accounts:profile', kwargs={'username': 'eve'}))

    def test_login_view_rejects_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'eve',
            'password': 'WrongPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_logout_view_logs_out_user(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/logout.html')
        follow = self.client.get(reverse('accounts:profile', kwargs={'username': 'eve'}))
        self.assertEqual(follow.status_code, 200)

    def test_account_activation_sent_redirects_for_confirmed_user(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:account_activation_sent'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accounts:profile', kwargs={'username': 'eve'}))

    def test_account_activation_sent_shows_page_for_unconfirmed_user(self):
        self.client.login(username='frank', password='StrongPass123')
        response = self.client.get(reverse('accounts:account_activation_sent'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/account_activation_sent.html')

    @patch('accounts.views.send_activation_email')
    def test_resend_activation_email_sends_message(self, mock_send):
        self.client.login(username='frank', password='StrongPass123')
        response = self.client.get(reverse('accounts:resend_activation_email'), follow=True)
        self.assertRedirects(response, reverse('accounts:account_activation_sent'))
        self.assertEqual(mock_send.call_count, 1)
        request_arg, user_arg = mock_send.call_args[0]
        self.assertEqual(request_arg.path, reverse('accounts:resend_activation_email'))
        self.assertEqual(user_arg, self.unconfirmed_user)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)

    @patch('accounts.views.send_activation_email')
    def test_resend_activation_email_redirects_for_confirmed_user(self, mock_send):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:resend_activation_email'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('core:index'))
        mock_send.assert_not_called()

    def test_activate_view_marks_email_confirmed_and_logs_in(self):
        uid = urlsafe_base64_encode(force_bytes(self.unconfirmed_user.pk))
        token = default_token_generator.make_token(self.unconfirmed_user)
        response = self.client.get(reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token}))
        self.assertRedirects(response, reverse('accounts:account_activation_complete'))
        self.unconfirmed_user.refresh_from_db()
        self.assertTrue(self.unconfirmed_user.profile.email_confirmed)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_activate_view_with_invalid_token_renders_error_template(self):
        uid = urlsafe_base64_encode(force_bytes(self.unconfirmed_user.pk))
        response = self.client.get(reverse('accounts:activate', kwargs={'uidb64': uid, 'token': 'invalid-token'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/account_activation_invalid.html')
        self.unconfirmed_user.refresh_from_db()
        self.assertFalse(self.unconfirmed_user.profile.email_confirmed)

    def test_account_activation_complete_template(self):
        response = self.client.get(reverse('accounts:account_activation_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/account_activation_complete.html')

    def test_password_change_requires_authentication(self):
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_password_change_page_for_authenticated_user(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_change.html')

    def test_password_change_updates_password(self):
        self.client.login(username='eve', password='StrongPass123')
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'StrongPass123',
            'new_password1': 'EvenStrongerPass123',
            'new_password2': 'EvenStrongerPass123',
        })
        self.assertRedirects(response, reverse('accounts:profile', kwargs={'username': 'eve'}))
        self.confirmed_user.refresh_from_db()
        self.assertTrue(self.confirmed_user.check_password('EvenStrongerPass123'))


class EmailVerificationMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = EmailVerificationMiddleware(lambda request: HttpResponse('OK'))
        self.confirmed_user = User.objects.create_user('gina', 'gina@example.com', 'StrongPass123')
        self.confirmed_user.profile.email_confirmed = True
        self.confirmed_user.profile.save()
        self.unconfirmed_user = User.objects.create_user('harry', 'harry@example.com', 'StrongPass123')

    def test_middleware_skips_anonymous_users(self):
        request = self.factory.get('/protected/')
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_redirects_unconfirmed_users(self):
        request = self.factory.get('/protected/')
        request.user = self.unconfirmed_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('accounts:account_activation_sent'))

    def test_middleware_allows_confirmed_users(self):
        request = self.factory.get('/protected/')
        request.user = self.confirmed_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_allows_explicit_whitelist_urls(self):
        request = self.factory.get(reverse('accounts:account_activation_sent'))
        request.user = self.unconfirmed_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_allows_prefix_whitelist(self):
        request = self.factory.get('/admin/dashboard/')
        request.user = self.unconfirmed_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendActivationEmailTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('irene', 'irene@example.com', 'StrongPass123')

    def test_send_activation_email_enqueues_message(self):
        request = self.factory.get('/')
        send_activation_email(request, self.user)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Activate Your Account')
        self.assertIn('accounts/activate', message.body)
        self.assertIn(urlsafe_base64_encode(force_bytes(self.user.pk)), message.body)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('john', 'john@example.com', 'StrongPass123')
        self.user.profile.email_confirmed = True
        self.user.profile.save()

    def test_password_reset_end_to_end(self):
        response = self.client.post(reverse('accounts:password_reset'), {'email': 'john@example.com'}, follow=True)
        self.assertTemplateUsed(response, 'registration/password_reset_done.html')
        self.assertEqual(len(mail.outbox), 1)

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(confirm_url, follow=True)
        form_url = response.redirect_chain[-1][0] if response.redirect_chain else confirm_url
        response = self.client.post(form_url, {
            'new_password1': 'ResetPass123',
            'new_password2': 'ResetPass123',
        }, follow=True)
        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        self.assertTemplateUsed(response, 'registration/password_reset_complete.html')

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetPass123'))
        self.assertTrue(self.client.login(username='john', password='ResetPass123'))
