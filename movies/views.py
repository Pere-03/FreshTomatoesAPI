from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, When

from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Movie
from . import serializers


@extend_schema(
    methods=["GET"],
    description="Retrieve a list of all movies",
    responses={
        200: OpenApiResponse(description="List of movies retrieved successfully"),
    },
)
@extend_schema(
    methods=["POST"],
    description="Create a new movie",
    responses={
        201: OpenApiResponse(description="New movie created successfully"),
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="User must be logged in to manage movies"),
        403: OpenApiResponse(description="Higher role needed to manage movies"),
    },
)
class MovieListView(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = serializers.MovieSerializer
    filter_backends = [filters.OrderingFilter]
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
            data = [get_movie_info(movie) for movie in page]
            return self.get_paginated_response(data)
        data = [get_movie_info(movie) for movie in queryset]
        return Response(data)

    def filter_queryset(self, queryset):
        query_params = self.request.query_params
        try:
            if "search" in query_params:
                search_term = query_params["search"]
                queryset_title_ids = list(
                    queryset.filter(title__icontains=search_term).values_list(
                        "id", flat=True
                    )
                )
                queryset_cast_ids = list(
                    queryset.filter(cast__name__icontains=search_term).values_list(
                        "id", flat=True
                    )
                )
                queryset_directors_ids = list(
                    queryset.filter(directors__name__icontains=search_term).values_list(
                        "id", flat=True
                    )
                )

                # The queryset is ordered by relevance in 'title', 'cast', and 'directors'.
                ids_ordered = (
                    queryset_title_ids
                    + [id for id in queryset_cast_ids if id not in queryset_title_ids]
                    + [
                        id
                        for id in queryset_directors_ids
                        if id not in queryset_title_ids and id not in queryset_cast_ids
                    ]
                )
                ordering = Case(
                    *[When(pk=pk, then=pos) for pos, pk in enumerate(ids_ordered)]
                )
                queryset = queryset.filter(id__in=ids_ordered).order_by(ordering)

                # Avoid django from default ordering.
                self.ordering = None
            else:
                # If 'search' is not present, the queryset is ordered by 'id'.
                self.ordering = ["id"]

            if "title" in query_params:
                queryset = queryset.filter(title__icontains=query_params["title"])

            if "cast" in query_params:
                queryset = queryset.filter(cast__name__icontains=query_params["cast"])

            if "director" in query_params:
                queryset = queryset.filter(
                    directors__name__icontains=query_params["director"]
                )

            if "genres" in query_params:
                queryset = queryset.filter(
                    genres__name__icontains=query_params["genres"]
                )

            if "rating" in query_params:
                queryset = queryset.filter(
                    rating__name__icontains=query_params["rating"]
                )

            if "year" in query_params:
                queryset = queryset.filter(year=query_params["year"])
            else:
                if "start" in query_params:
                    queryset = queryset.filter(year__gte=query_params["start"])
                if "end" in query_params:
                    queryset = queryset.filter(year__lte=query_params["end"])
        except (ValueError, TypeError):
            raise ValidationError("The query parameters must be of the correct type.")
        return super().filter_queryset(queryset)


@extend_schema(
    methods=["GET"],
    description="Retrieve information of a specific movie",
    responses={
        200: OpenApiResponse(description="Movie information retrieved successfully"),
        401: OpenApiResponse(description="User must be logged in to manage movies"),
    },
)
@extend_schema(
    methods=["PUT", "PATCH"],
    description="Update information of a specific movie",
    responses={
        200: OpenApiResponse(description="Movie information updated successfully"),
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="User must be logged in to manage movies"),
        403: OpenApiResponse(description="Higher role needed to manage movies"),
    },
)
@extend_schema(
    methods=["DELETE"],
    description="Delete a specific movie",
    responses={
        204: OpenApiResponse(description="Movie deleted successfully"),
        401: OpenApiResponse(description="User must be logged in to manage movies"),
        403: OpenApiResponse(description="Higher role needed to manage movies"),
    },
)
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


def get_movie_info(movie):
    return {
        "id": str(movie.id),
        "title": movie.title,
        "year": movie.year,
        "runtime": movie.runtime if movie.runtime is not None else "--",
        "userRating": movie.userRating,
        "votes": movie.votes,
        "poster": movie.poster,
    }


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
