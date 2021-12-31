import datetime
import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from Users.models import User

logger = logging.getLogger(__name__)

FORBIDDEN = status.HTTP_403_FORBIDDEN
NOT_FOUND = status.HTTP_404_NOT_FOUND

def send_verification_email(user):
    token = user.generate_verification_token()
    email_data = {'name': user.first_name + ' ' + user.last_name,
                    'id': user.id,
                    'token': token}
    template = render_to_string('verify_email.html', email_data)
    email = EmailMultiAlternatives('Verify your email',
                                    '',
                                    settings.EMAIL_HOST_USER,
                                    [user.email])
    email.attach_alternative(template, "text/html")
    email.fail_silently = False
    email.send()
    logger.warning(f'Users App | New user, verification email sent to' \
                    '{user.email} at {datetime.datetime.now()}')

def send_reset_password_email(reset_password_token):
    # TODO: change email to actually send a front url with token generated to reset password
    token = f"{reset_password_token.key}"
    name = reset_password_token.user.first_name
    email_data = {'name': name,
                    'token': token}
    template = render_to_string('reset_password.html', email_data)
    email = EmailMultiAlternatives('Verify your email',
                                    '',
                                    settings.EMAIL_HOST_USER,
                                    [reset_password_token.user.email])
    email.attach_alternative(template, "text/html")
    email.fail_silently = False
    email.send()
    logger.warning(f'Users App | Password restore, email sent to' \
                     '{reset_password_token.user.email} at {datetime.datetime.now()}')

def get_user_or_error(request_user, pk):
    """
    Get user or return error
    """
    error, instance = None, None
    try:
        instance = User.objects.get(id=pk)
    except User.DoesNotExist:
        error = Response("User not found", status=NOT_FOUND)
    if not request_user.is_admin and request_user.id != instance.id:
        error = Response("You don't have permission", status=FORBIDDEN)
    if not request_user.is_verified:
        error = Response("You have to verify your account first", status=FORBIDDEN)
    return instance, error