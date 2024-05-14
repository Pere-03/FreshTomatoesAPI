from django.urls import path
from . import views

urlpatterns = [
    path("", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("me", views.UserView.as_view(), name="me"),
    path("logout", views.LogoutView.as_view(), name="logout"),
]
