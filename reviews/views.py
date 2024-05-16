from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Review
from users.models import TomatoeUser
from movies.models import Movie
from .serializers import ReviewSerializer


@extend_schema(
    methods=['GET'],
    description="Retrieve a list of all reviews",
    responses={
        200: OpenApiResponse(description="List of reviews retrieved successfully"),
    },
)
@extend_schema(
    methods=['POST'],
    description="Create a new review",
    responses={
        201: OpenApiResponse(description="New review created successfully"),
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="User must be logged in to manage reviews"),
    },
)
class ReviewListView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["userRating"]
    ordering = ["id"]

    def post(self, request):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            movie = serializer.validated_data.get("movie")
            review = Review.objects.filter(user=user, movie=movie).first()
            overwrite = request.data.get("overwrite", False)

            if review is not None:
                if overwrite:
                    for attr, value in serializer.validated_data.items():
                        setattr(review, attr, value)
                    review.save()
                    self.update_rating(movie, review)
                    return Response(
                        get_review_data(review).data,
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        ReviewSerializer(review).data,
                        status=status.HTTP_409_CONFLICT,
                    )
            else:
                review = serializer.save(user=user)
                self.update_rating(movie, review)
                return Response(
                    get_review_data(review),
                    status=status.HTTP_201_CREATED,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def filter_queryset(self, queryset):
        query_params = self.request.query_params

        if "movie_id" in query_params:
            queryset = queryset.filter(movie__id=query_params["movie_id"])
        elif "title" in query_params:
            queryset = queryset.filter(movie__title__icontains=query_params["title"])

        if "user_id" in query_params:
            queryset = queryset.filter(user__id=query_params["user_id"])
        elif "username" in query_params:
            queryset = queryset.filter(
                user__username__icontains=query_params["username"]
            )

        return super().filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [get_review_data(review) for review in page]
            return self.get_paginated_response(data)
        data = [get_review_data(review) for review in queryset]
        return Response(data)

    def update_rating(self, movie, review):
        """
        Updates movie rating according to new review rating
        """

        movie.userRating = (movie.userRating * movie.votes + review.userRating) / (
            movie.votes + 1
        )
        movie.votes = movie.votes + 1
        movie.save()
        return


@extend_schema(
    methods=['GET'],
    description="Retrieve a specific review",
    responses={
        200: OpenApiResponse(description="Review information retrieved successfully"),
        401: OpenApiResponse(description="User must be logged in to manage reviews"),
    },
)
@extend_schema(
    methods=['PUT', 'PATCH'],
    description="Update a specific review",
    responses={
        200: OpenApiResponse(description="Review information updated successfully"),
        400: OpenApiResponse(description="Invalid data"),
        401: OpenApiResponse(description="User must be logged in to manage reviews"),
        403: OpenApiResponse(description="User can only edit their own reviews"),
    },
)
@extend_schema(
    methods=['DELETE'],
    description="Delete a specific review",
    responses={
        204: OpenApiResponse(description="Review deleted successfully"),
        401: OpenApiResponse(description="User must be logged in to manage reviews"),
        403: OpenApiResponse(description="User can only delete their own reviews"),
    },
)
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        instance = self.get_object()
        data = get_review_data(instance)
        return Response(data)

    def put(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        instance = self.get_object()
        if user.id != instance.user.id:
            return Response(
                {"detail": "Can only edit your own reviews."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = check_update(request.data, instance)
        if isinstance(data, Response):
            return data
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(get_review_data(review))

    def update(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user

        instance = self.get_object()
        if user.id != instance.user.id:
            return Response(
                {"detail": "Can only edit your own reviews."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = check_update(request.data, instance)
        if isinstance(data, Response):
            return data
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(get_review_data(review))

    def delete(self, request, *args, **kwargs):
        user = get_user(self.request)
        if isinstance(user, Response):
            return user
        instance = self.get_object()
        if user.id != instance.user.id:
            return Response(
                {"detail": "User can only delete your own reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().delete(request, *args, **kwargs)


def check_update(data, instance):
    if "user" in data:
        if not isinstance(data["user"], int):
            data["user"] = data["user"]["id"]
        if data["user"] != instance.user.id:
            return Response(
                {"detail": "User can only delete your own reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )
    if "movie" in data:
        if not isinstance(data["movie"], int):
            data["movie"] = data["movie"]["id"]
        if data["movie"] != instance.movie.id:
            return Response(
                {"detail": "Cannot change Review's movie."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        data["movie"] = instance.movie.id
    return data


def get_user(request):
    try:
        user = Token.objects.get(key=request.COOKIES.get("session")).user

        if user is None:
            return Response(
                {"detail": "User must be logged in to manage reviews."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return user

    except ObjectDoesNotExist:
        return Response(
            {"detail": "User must be logged in to manage reviews."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


def get_review_data(review):
    if isinstance(review.movie, Movie):
        movie = review.movie
    else:
        movie = Movie.objects.get(id=review.movie)
    if isinstance(review.user, TomatoeUser):
        user = review.user
    else:
        user = TomatoeUser.objects.get(id=review.user)
    return {
        "id": review.id,
        "movie": {"id": movie.id, "title": movie.title},
        "user": {"id": user.id, "username": user.username},
        "userRating": review.userRating,
        "comment": review.comment,
    }
