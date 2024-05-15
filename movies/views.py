from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from .models import Movie
from . import serializers


class MovieListView(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = serializers.MovieSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["title", "cast__name", "directors__name"]
    ordering_fields = ["year", "userRating", "runtime", "votes"]
    ordering = ["id"]

    def post(self, request):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            movie = serializer.save()
            return Response(get_movie_data(movie), status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [get_movie_data(movie) for movie in page]
            return self.get_paginated_response(data)
        data = [get_movie_data(movie) for movie in queryset]
        return Response(data)

    def filter_queryset(self, queryset):
        query_params = self.request.query_params
        try:
            if "genres" in query_params:
                queryset = queryset.filter(
                    genres__name__icontains=query_params["genres"]
                )

            if "rating" in query_params:
                queryset = queryset.filter(
                    rating__name__icontains=query_params["rating"]
                )

            if "year" in query_params:
                queryset = queryset.filter(
                    year=query_params['year']
                )
            else:
                if "start" in query_params:
                    queryset = queryset.filter(
                        year__gte=query_params["start"]
                    )
                if "end" in query_params:
                    queryset = queryset.filter(
                        year__lte=query_params["end"]
                    )
        except (ValueError, TypeError):
            raise ValidationError(
                "Los parámetros de consulta deben ser del tipo correcto."
            )
        return super().filter_queryset(queryset)


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = serializers.MovieSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        data = get_movie_data(instance)
        return Response(data)

    def put(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        instance = self.get_object()
        data = revert_movie(request.data)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        movie = serializer.save()
        return Response(get_movie_data(movie))

    def update(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        instance = self.get_object()
        data = revert_movie(request.data)
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        movie = serializer.save()
        return Response(get_movie_data(movie))

    def delete(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        return super().delete(request, *args, **kwargs)


def get_user(request):
    try:
        user = Token.objects.get(key=request.COOKIES.get("session")).user

        if user is None:
            return Response(
                {"detail": "User must be logged in to manage movies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        elif not user.is_staff:
            return Response(
                {"detail": "Higher role needed to manage movies"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return user

    except ObjectDoesNotExist:
        return Response(
            {"detail": "User must be logged in to manage movies."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


def get_movie_data(movie):
    return {
        "id": str(movie.id),
        "title": movie.title,
        "year": movie.year,
        "runtime": movie.runtime if movie.runtime is not None else "--",
        "rating": {"id": movie.rating.id, "rating": movie.rating.name}
        if movie.rating.name is not None
        else {"id": -1, "rating": "--"},
        "directors": [
            {"id": director.id, "name": director.name}
            for director in movie.directors.all()
        ],
        "userRating": movie.userRating,
        "votes": movie.votes,
        "genres": [
            {"id": genre.id, "genre": genre.name} for genre in movie.genres.all()
        ],
        "cast": [{"id": actor.id, "name": actor.name} for actor in movie.cast.all()],
        "poster": movie.poster,
    }


def revert_movie(data):
    if "directors" in data and not isinstance(data["directors"][0], int):
        data["directors"] = [director["id"] for director in data["directors"]]
    if "rating" in data and not isinstance(data["rating"], int):
        data["rating"] = data["rating"]["id"]
    if "cast" in data and not isinstance(data["cast"][0], int):
        data["cast"] = [actor["id"] for actor in data["cast"]]
    if "genres" in data and not isinstance(data["genres"][0], int):
        data["genres"] = [genre["id"] for genre in data["genres"]]
    return data
