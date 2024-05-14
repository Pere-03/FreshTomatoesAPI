from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotAuthenticated

from .models import Review
from users.models import TomatoeUser
from movies.models import Movie
from .serializers import ReviewSerializer


class ReviewListView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def post(self, request):
        try:
            user = Token.objects.get(key=self.request.COOKIES.get("session")).user
            if user is None:
                raise NotAuthenticated("User must be logged in to make a review.")
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
                            ReviewSerializer(review).data,
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
                        self.get_review_data(review),
                        status=status.HTTP_201_CREATED,
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_queryset(self):
        queryset = Review.objects.all().order_by("id")
        movie_id = self.kwargs.get("movie_pk")
        if "me" in self.request.path:
            try:
                user = Token.objects.get(key=self.request.COOKIES.get("session")).user
                if user is None:
                    raise NotAuthenticated(
                        "User must be logged in to view their reviews."
                    )
                queryset = queryset.filter(user=user)
            except ObjectDoesNotExist:
                raise NotAuthenticated("User must be logged in to view their reviews.")

        if movie_id is not None:
            queryset = queryset.filter(movie__id=movie_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self.get_review_data(review) for review in page]
            return self.get_paginated_response(data)
        data = [self.get_review_data(review) for review in queryset]
        return Response(data)

    def get_review_data(self, review):
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
            "comment": review.comment,
        }

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


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
