from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from users import serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse


class RegisterView(generics.CreateAPIView):
    serializer_class = serializers.UserSerializer

    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            return Response(status=status.HTTP_409_CONFLICT)
        return super().handle_exception(exc)


class LoginView(generics.CreateAPIView):
    serializer_class = serializers.LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            token, _ = Token.objects.get_or_create(user=serializer.validated_data)
            response = Response(status=status.HTTP_201_CREATED)

            response.set_cookie(
                key="session",
                value=token.key,
                secure=True,
                httponly=True,
                samesite="None",
            )
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class UserView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return Token.objects.get(key=self.request.COOKIES.get("session")).user

    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super().handle_exception(exc)


@extend_schema(
    description="Logout endpoint",
    responses={
        204: OpenApiResponse(description="User has logged out succesfuly"),
        401: OpenApiResponse(description="No user logged"),
    },
)
class LogoutView(generics.DestroyAPIView):
    def delete(self, request):
        token = Token.objects.get(key=request.COOKIES.get("session"))
        token.delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("session")
        return response

    def handle_exception(self, exc):
        if isinstance(exc, ObjectDoesNotExist):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super().handle_exception(exc)
