from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotAuthenticated

from .models import Review
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
                    new_review = serializer.save(user=user)
                    self.update_rating(movie, new_review)
                    return Response(
                        self.ger_review_data(review),
                        status=status.HTTP_201_CREATED,
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_queryset(self):
        queryset = Review.objects.all()
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
