import json

from django.contrib.auth import get_user_model
from django_rest_passwordreset.models import ResetPasswordToken
from django.test import TestCase
from rest_framework.test import APIClient

from Users.models import User

ENDPOINT = '/api/v1/users'


class UsersAbstractUtils(TestCase):

    def setUp(self):
        self._clean()
        self.admin_user = self._create_user(is_admin=True, **{
            'email': 'adminuser@appname.me',
            'phone_number': '+34123456789'})
        self.normal_user = self._create_user(**{
            'email': 'normaluser@appname.me',
            'phone_number': '+032923093'})
        self.client = APIClient()

    def _create_user(self, is_admin=False, **kwargs):
        first_name = kwargs.get('name', 'Name')
        last_name = kwargs.get('last_name', 'Last Name')
        email = kwargs.get('email', 'user@appname.me')
        password = kwargs.get('password', 'password')
        is_admin = kwargs.get('is_admin', is_admin)
        phone_number = kwargs.get('phone_number', '+1234567890')
        user =  User.objects.create_user(first_name = first_name,
                                        last_name = last_name,
                                        email = email,
                                        password ='',
                                        is_admin = is_admin,
                                        is_verified = is_admin,
                                        phone_number = phone_number)
        user.set_password(password)
        user.save()
        return user

    def _clean(self):
        User.objects.all().delete()


class UsersManagersTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email='normaluser@test.com',
            first_name='test_name',
            last_name='test_last_name',
            password='test_password'
        )
        self.assertEqual(user.email, 'normaluser@test.com')
        self.assertTrue(user.is_active)
        self.assertIsNone(user.username)
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email='')
        with self.assertRaises(TypeError):
            User.objects.create_user(email='', password="foo")

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            email='super@user.com',
            password='test_password',
            first_name='test_name',
            last_name='test_last_name'
        )
        self.assertEqual(admin_user.email, 'super@user.com')
        self.assertTrue(admin_user.is_verified)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_superuser(
                email='super@user.com',
                first_name='test_name',
                last_name='test_last_name'
            )


class UserTests(UsersAbstractUtils):

    def test_list_users(self):
        # Test that an unauthenticated user can't list users data
        response = self.client.get(f'{ENDPOINT}/', format='json')
        self.assertEqual(response.status_code, 401)

        # Test that the petition with admin user is valid and returns the 2 users from setup
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'{ENDPOINT}/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        # Test that the petition with normal user is denied
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(f'{ENDPOINT}/', format='json')
        self.assertEqual(response.status_code, 403)

        # Test a petition with normal normal user verified is denied
        self.normal_user.is_verified = True
        self.normal_user.save()
        response = self.client.get(f'{ENDPOINT}/', format='json')
        self.assertEqual(response.status_code, 403)

    def test_get_user(self):
        # Test that an unauthenticated user can't get users data
        response = self.client.get(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 401)

        # Test a petition with normal user not verified to its user is denied
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 403)

        # Test a petition with normal user verified is granted to its data
        self.normal_user.is_verified = True
        self.normal_user.save()
        response = self.client.get(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.normal_user.id)
        self.assertEqual(response.data["email"], self.normal_user.email)

        # Test a petition with normal user verified is denied to other user's data
        response = self.client.get(f'{ENDPOINT}/{self.admin_user.id}/', format='json')
        self.assertEqual(response.status_code, 403)

        # Test a petition with admin user is granted to other user's data
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 200)

    def test_sign_up(self):
        # Test that cannot signup with an used email
        self._create_user(**{'email': 'emailused@appname.me'})
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"emailused@appname.me",
            "password":"password",
            "password_confirmation":"password"
        }
        response = self.client.post(f'{ENDPOINT}/signup/', data, format='json')
        message_one = 'email'
        message_two = 'This field must be unique'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message_one in response.data)
        self.assertTrue(message_two in response.data['email'][0])

        # Test that cant sign up with a common password
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"unusedemail@appname.me",
            "password":"password",
            "password_confirmation":"password"
        }
        response = self.client.post(f'{ENDPOINT}/signup/', data, format='json')
        message = 'This password is too common.'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data['non_field_errors'][0])

        # Test that cant sign up
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"unusedemail@appname.me",
            "password":"strongpassword",
            "password_confirmation":"strongpassword"
        }
        self.assertEqual(User.objects.count(), 3)
        response = self.client.post(f'{ENDPOINT}/signup/', data, format='json')
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['first_name'], data['first_name'])
        self.assertEqual(response.data['last_name'], data['last_name'])
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['phone_number'], '')
        self.assertEqual(response.data['is_verified'], False)
        self.assertEqual(response.data['is_admin'], False)
        self.assertEqual(response.data['is_premium'], False)

        # Test that special fields cant be setted up in sign up accepted request
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"unusedemail2@appname.me",
            "password":"strongpassword",
            "password_confirmation":"strongpassword",
            "phone_number": "+03999999999",
            "is_verified": True,
            "is_admin": True,
            "is_premium": True
        }
        self.assertEqual(User.objects.count(), 4)
        response = self.client.post(f'{ENDPOINT}/signup/', data, format='json')
        self.assertEqual(User.objects.count(), 5)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['first_name'], data['first_name'])
        self.assertEqual(response.data['last_name'], data['last_name'])
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['phone_number'], '')
        self.assertEqual(response.data['is_verified'], False)
        self.assertEqual(response.data['is_admin'], False)
        self.assertEqual(response.data['is_premium'], False)

    def test_update_user(self):
        # Set data test for update
        data = {
            "first_name":"Test edited",
            "last_name":"Tested Edit",
            "email":"edituser2@appname.me",
            "phone_number": "+32987654321",
            "old_password": "password",
            "password":"NewPassword95"
        }
        # Test that an unauthenticated user can't update users data
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # Test that an unverified user can't update its data
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 403)
        self.normal_user.is_verified = True
        self.normal_user.save()

        # Test that a verified user can't update other's data
        response = self.client.put(f'{ENDPOINT}/{self.admin_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.normal_user.email, data["email"])

        # Test that a verified user can update its data
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 202)
        self.normal_user = User.objects.get(id=self.normal_user.id)
        self.assertEqual(self.normal_user.email, data["email"])
        self.assertEqual(self.normal_user.phone_number, data["phone_number"])
        self.assertEqual(self.normal_user.first_name, data["first_name"])
        self.assertEqual(self.normal_user.last_name, data["last_name"])
        self.assertTrue(self.normal_user.check_password(data["password"]))
        self.client.force_authenticate(user=self.normal_user)

        # Test that an user verified can't update its email to one already used
        self._create_user(**{'email': 'emailused@appname.me'})
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"emailused@appname.me",
            "password":"password"
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue("Email is taken" in response.data)

        # Test that an user verified can't update its phone to one already used
        self._create_user(**{'phone_number': '+03999999999'})
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"edituser3@appname.me",
            "password":"password",
            "phone_number": "+03999999999"
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue("Phone number is taken" in response.data)

        # Test a user can't update its password with a wrong old password
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"finalemail@appname.me",
            "phone_number": "+32987654321",
            "old_password": "NewPassword95 wrong",
            "password":"This is a password"
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        message = "Wrong password"
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data)

        # Test a user can't update its password without the old one
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"finalemail@appname.me",
            "phone_number": "+32987654321",
            "password":"This is a password"
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        message = 'Old password is required to set a new one'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data)

        # Test a user can't update special fields on a valid request
        data = {
            "first_name":"Test",
            "last_name":"Tested",
            "email":"emailemail@appname.me",
            "phone_number": "+32987654321",
            "old_password":"NewPassword95",
            "password":"This is a password",
            "is_verified": False,
            "is_admin": True,
            "is_premium": True
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 202)
        self.normal_user = User.objects.get(id=self.normal_user.id)
        self.assertEqual(self.normal_user.email, data["email"])
        self.assertEqual(self.normal_user.phone_number, data["phone_number"])
        self.assertEqual(self.normal_user.first_name, data["first_name"])
        self.assertEqual(self.normal_user.last_name, data["last_name"])
        self.assertTrue(self.normal_user.check_password(data["password"]))
        self.assertEqual(self.normal_user.is_verified, True)
        self.assertEqual(self.normal_user.is_admin, False)
        self.assertEqual(self.normal_user.is_premium, False)
        self.client.force_authenticate(user=self.normal_user)

        # Test a user can update only the password with the old one
        data = {
            "old_password":"This is a password",
            "password":"Password 123456789"
        }
        response = self.client.put(f'{ENDPOINT}/{self.normal_user.id}/', data, format='json')
        self.assertEqual(response.status_code, 202)
        self.normal_user = User.objects.get(id=self.normal_user.id)
        self.assertTrue(self.normal_user.check_password(data["password"]))

    def test_delete_user(self):
        # Test that an unauthenticated user can't delete users data
        self.assertEqual(User.objects.count(), 2)
        response = self.client.delete(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(User.objects.count(), 2)

        # Test that an unverified user can't delete its data
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.delete(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 2)

        # Test that a verified user can't delete other's data
        self.normal_user.is_verified = True
        self.normal_user.save()
        response = self.client.delete(f'{ENDPOINT}/{self.admin_user.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 2)

        # Test that a verified user can delete its data
        response = self.client.delete(f'{ENDPOINT}/{self.normal_user.id}/', format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(User.objects.count(), 1)

    def test_log_in(self):
        testing_user = self._create_user(**{
            'email': 'rightemail@appname.me',
            'password': 'RightPassword'
        })

        # Test that cannot log in with an invalid email
        data = {
            'email': 'wroongemail@appname.me',
            'password': 'RightPassword'
        }
        response = self.client.post(f'{ENDPOINT}/login/', data, format='json')
        message = 'Invalid credentials'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data['non_field_errors'][0])

        # Test that cannot log in with an invalid password
        data = {
            'email': 'rightemail@appname.me',
            'password': 'WrongPassword'
        }
        response = self.client.post(f'{ENDPOINT}/login/', data, format='json')
        message = 'Invalid credentials'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data['non_field_errors'][0])

        # Test that user not verified cannot log in
        data = {
            'email': 'rightemail@appname.me',
            'password': 'RightPassword'
        }
        response = self.client.post(f'{ENDPOINT}/login/', data, format='json')
        message = 'User is not verified'
        self.assertEqual(response.status_code, 400)
        self.assertTrue(message in response.data['non_field_errors'][0])

        # Test that user verified can log in
        testing_user.is_verified = True
        testing_user.save()
        data = {
            'email': 'rightemail@appname.me',
            'password': 'RightPassword'
        }
        response = self.client.post(f'{ENDPOINT}/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('token' in data)
        self.assertTrue('user' in data)
        self.assertEqual(data['user']['first_name'], testing_user.first_name)
        self.assertEqual(data['user']['last_name'], testing_user.last_name)
        self.assertEqual(data['user']['email'], testing_user.email)

    def test_verify_user(self):
        # Test that any user can verify its user with a get
        # request with it id and token
        token = self.normal_user.generate_verification_token()
        self.assertEqual(self.normal_user.is_verified, False)
        response = self.client.get(f'{ENDPOINT}/{self.normal_user.id}/verify/?token={token}')
        self.assertEqual(response.status_code, 202)
        normal_user_updated = User.objects.get(id=self.normal_user.id)
        self.assertEqual(normal_user_updated.is_verified, True)

    def test_reset_password(self):
        # Test that any user can reset its password via API
        self.assertTrue(self.normal_user.check_password('password'))
        response = self.client.post(f'/api/v1/password_reset/', {'email': self.normal_user.email})
        self.assertEqual(response.status_code, 200)
        tokens = ResetPasswordToken.objects.all()
        self.assertEqual(len(tokens), 1)
        token = tokens[0].key
        data = {
            'token': token,
            'password': 'NewPassword95'
        }
        self.client.post(f'/api/v1/password_reset/confirm/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.normal_user = User.objects.get(id=self.normal_user.id)
        self.assertTrue(self.normal_user.check_password('NewPassword95'))
