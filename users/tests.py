from rest_framework.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import TomatoeUser
from users.serializers import UserSerializer


class TestUserModel(TestCase):
    def setUp(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )

    def test_user_creation(self):
        self.assertEqual(TomatoeUser.objects.count(), 1)


class TestUserSerializer(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "terminator",
            "name": "Test User",
            "tel": "123456789",
            "email": "testuser@test.com",
            "password": "Testpassword1"
        }
        self.inputs = ["Hol12ascs", "vadsvadsad", "Hol12"]
        self.expects_error = [False, True, True]
        self.serializer = UserSerializer(data=self.user_data)

    def test_validate_password(self):
        for inp, error in zip(self.inputs, self.expects_error):
            if error:
                with self.assertRaises(ValidationError):
                    self.serializer.validate_password(inp)
            else:
                self.assertEqual(self.serializer.validate_password(inp), inp)

    def test_validate_password_short(self):
        self.user_data["password"] = "Short1"
        serializer = UserSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["password"][0],
            "Password must contain at least 8 characters",
        )

    def test_validate_password_no_uppercase(self):
        self.user_data["password"] = "testpassword1"
        serializer = UserSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["password"][0], "Invalid password format")

    def test_validate_password_no_lowercase(self):
        self.user_data["password"] = "TESTPASSWORD1"
        serializer = UserSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["password"][0], "Invalid password format")

    def test_validate_password_no_number(self):
        self.user_data["password"] = "TestPassword"
        serializer = UserSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["password"][0], "Invalid password format")


class TestRegisterView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.user_data = {
            "username": "terminator",
            "name": "Test User",
            "tel": "123456789",
            "email": "testuser@test.com",
            "password": "Testpassword1",
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

    def test_register_user_duplicate(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # If username already exists
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # If email already exists
        self.user_data['username'] = 'NotDuplicated'
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class TestLoginView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )
        self.user_data = {"email": "testuser@test.com", "password": "Testpassword1"}

    def test_login_user(self):
        response = self.client.post(self.login_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("session", response.cookies)

    def test_login_user_wrong_password(self):
        self.user_data["password"] = "WrongPassword1"
        response = self.client.post(self.login_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLogoutView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )
        self.user_data = {"email": "testuser@test.com", "password": "Testpassword1"}

    def test_logout_user(self):
        response = self.client.post(self.login_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("session", response.cookies)
        self.assertNotEqual(response.cookies["session"].value, "")

        response = self.client.delete(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.cookies["session"].value, "")


class TestUserView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.user_view_url = reverse("me")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )
        self.user_data = {"email": "testuser@test.com", "password": "Testpassword1"}

    def test_user_view_without_login(self):
        response = self.client.get(self.user_view_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_view_with_login(self):
        self.client.post(self.login_url, self.user_data, format="json")
        response = self.client.get(self.user_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_data["email"])

    def test_user_view_after_logout(self):
        self.client.post(self.login_url, self.user_data, format="json")
        self.client.delete(self.logout_url)
        response = self.client.get(self.user_view_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
