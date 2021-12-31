import base64
import hashlib
import logging

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.utils.translation import gettext_lazy as _

from django.conf import settings

logger = logging.getLogger(__name__)

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, first_name, last_name, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          first_name=first_name,
                          last_name=last_name,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        user = self.model(email=email,
                        first_name=first_name,
                        last_name=last_name,
                        **extra_fields)
        user.set_password(password)
        user.is_admin = True
        user.is_verified = True
        user.is_premium = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    username = None
    is_superuser = None

    email = models.EmailField('Email address',
                                unique = True,
                                error_messages = {
                                    'unique': 'This email already exists.'
                                })
    first_name = models.CharField('First name',
                                blank = False,
                                max_length = 50)
    last_name = models.CharField('Last name',
                                blank = False,
                                max_length = 50)
    phone_number = models.CharField('User number',
                                blank = True,
                                max_length = 15)
    is_verified = models.BooleanField('Verification status',
                                    default = False)
    is_premium = models.BooleanField('Premium status',
                                    default = False)
    is_admin = models.BooleanField('Admin status',
                                    default = False)
    created_at = models.DateTimeField('Creation date',
                                    auto_now_add=True)
    updated_at = models.DateTimeField('Update date',
                                    auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def generate_verification_token(self):
        string_user = self.email + settings.EMAIL_VERIFICATION_TOKEN_SECRET
        hashed = hashlib.md5(string_user.encode())
        decoded = base64.b64encode(hashed.digest()).decode('utf-8')
        token = decoded.replace("\+", "-").replace("/", "_")\
                       .replace("=", "").replace("+","")
        return token

    @property
    def name(self):
        return self.first_name + " " + self.last_name

    @property
    def is_staff(self):
        return self.is_admin


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    from Users.utils import send_reset_password_email
    send_reset_password_email(reset_password_token)