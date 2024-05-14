from django.urls import path
from . import views

urlpatterns = [
    path("", views.ReviewListView.as_view(), name="review_list"),
    path("<int:pk>/", views.ReviewDetailView.as_view(), name="review_detail"),
]
