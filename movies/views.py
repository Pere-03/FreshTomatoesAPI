from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from .models import Movie
from . import serializers


class MovieListView(generics.ListCreateAPIView):
    serializer_class = serializers.MovieSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["year", "userRating", "runtime"]

    def post(self, request):
        try:
            user = Token.objects.get(key=self.request.COOKIES.get("session")).user

            if user is None:
                return Response(
                    {"detail": "User must be logged in to make a review."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            elif not user.is_staff:
                return Response(
                    {"detail": "Higher role needed to add a movie"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "User must be logged in to make a review."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [get_movie_data(movie) for movie in page]
            return self.get_paginated_response(data)
        data = [get_movie_data(movie) for movie in queryset]
        return Response(data)

    def get_queryset(self):
        queryset = Movie.objects.all()
        movie_id = self.kwargs.get("movie_pk")
        if movie_id is not None:
            queryset = queryset.filter(id=movie_id)
        return self.filter_queryset(queryset)

    def filter_queryset(self, queryset):
        query_params = self.request.query_params
        try:
            if "title" in query_params:
                queryset = queryset.filter(title__icontains=query_params["title"])

            if "genre" in query_params:
                queryset = queryset.filter(
                    genres__name__icontains=query_params["genre"]
                )

            if "cast" in query_params:
                queryset = queryset.filter(cast__name__icontains=query_params["cast"])

            if "director" in query_params:
                queryset = queryset.filter(
                    directors__name__icontains=query_params["director"]
                )

            if "rating" in query_params:
                queryset = queryset.filter(rating__name__icontains=query_params["rating"])

        except (ValueError, TypeError):
            raise ValidationError(
                "Los parámetros de consulta deben ser del tipo correcto."
            )
        return super().filter_queryset(queryset)


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.MovieSerializer
    lookup_field = 'movie_pk'

    def get_queryset(self):
        queryset = Movie.objects.all()
        movie_id = self.kwargs.get('movie_pk')

        if movie_id is not None:
            queryset = queryset.filter(id=movie_id)
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {"pk": self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)

        return obj

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        data = get_movie_data(instance)
        return Response(data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def get_movie_data(movie):
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "runtime": movie.runtime if movie.runtime is not None else "--",
        "rating": movie.rating.name if movie.rating.name is not None else "--",
        "directors": [director.name for director in movie.directors.all()],
        "userRating": movie.userRating,
        "votes": movie.votes,
        "genres": [genre.name for genre in movie.genres.all()],
        "cast": [actor.name for actor in movie.cast.all()],
        "poster": movie.poster,
    }