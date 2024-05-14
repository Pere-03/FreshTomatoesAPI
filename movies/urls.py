from django.urls import path
from . import views

urlpatterns = [
    path("", views.MovieListView.as_view(), name="movie_list"),
    path("<int:movie_pk>/", views.MovieDetailView.as_view(), name="movie_detail"),
]
