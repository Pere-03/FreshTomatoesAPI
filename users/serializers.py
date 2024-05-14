import re
from rest_framework import serializers, exceptions
from django.contrib.auth import authenticate
from django.db.utils import IntegrityError
from users import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TomatoeUser
        fields = ["id", "name", "username", "tel", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["id"]

    def validate_password(self, value):
        if len(value) < 8:
            raise exceptions.ValidationError(
                "Password must contain at least 8 characters"
            )
        elif re.match("^(?=.*[0-9])(?=.*[A-Z])(?=.*[a-z]).*$", value) is None:
            raise exceptions.ValidationError("Invalid password format")
        else:
            return value

    def create(self, validated_data):
        if models.TomatoeUser.objects.filter(
            email=validated_data.get("email")
        ).exists():
            raise IntegrityError("Email already registered for another user")

        return models.TomatoeUser.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("password"):
            instance.set_password(validated_data.pop("password"))
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username", None)
        password = data.get("password", None)

        if username is None:
            raise exceptions.ValidationError("Username is required.")

        if password is None:
            raise exceptions.ValidationError("Password is required.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise exceptions.ValidationError("User not found, check credentials.")

        return user
