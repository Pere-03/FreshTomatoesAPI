from rest_framework.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from users import serializers


class TestUserSerializer(SimpleTestCase):
    def test_validate_password(self):
        inputs = ["Hol12ascs", "vadsvadsad", "Hol12"]
        expects_error = [False, True, True]
        tested_unit = serializers.UserSerializer()
        for inp, error in zip(inputs, expects_error):
            if error:
                with self.assertRaises(ValidationError):
                    tested_unit.validate_password(inp)
            else:
                self.assertEqual(tested_unit.validate_password(inp), inp)


class TestRegisterView(TestCase):
    def test_caso_1_vista(self):
        response = self.client.post(
            "/api/users/",
            {
                "name": "Alvaro",
                "tel": "9999999",
                "email": "patata@pato.com",
                "password": "Abc12cb123",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
