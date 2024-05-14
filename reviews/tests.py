from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from movies.models import Movie, Genre, Celebrity, Rating
from users.models import TomatoeUser
from reviews.models import Review


class TestReviewModel(TestCase):
    def setUp(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.movie = Movie.objects.create(
            title="Test Movie",
            year=2020,
            rating=self.rating,
            runtime=120,
            userRating=7.5,
            votes=1000,
        )
        self.movie.genres.add(self.genre)
        self.movie.directors.add(self.celebrity)
        self.movie.cast.add(self.celebrity)
        self.review = Review.objects.create(
            user=self.user, movie=self.movie, userRating=8.0, comment="Great movie!"
        )

    def test_review_creation(self):
        self.assertEqual(Review.objects.count(), 1)


class TestReviewListView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.review_list_url = reverse("review_list")

    def test_review_list_without_login(self):
        response = self.client.get(self.review_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestReviewCreateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.review_list_url = reverse("review_list")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            name="Test User",
            tel="123456789",
            email="testuser@test.com",
            password="Testpassword1",
        )
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.movie = Movie.objects.create(
            title="Test Movie",
            year=2020,
            rating=self.rating,
            runtime=120,
            userRating=7.5,
            votes=1000,
        )
        self.movie.genres.add(self.genre)
        self.movie.directors.add(self.celebrity)
        self.movie.cast.add(self.celebrity)
        self.review_data = {
            "movie": self.movie.id,
            "userRating": 8.0,
            "comment": "Great movie!",
        }

    def test_review_create_without_login(self):
        response = self.client.post(
            self.review_list_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_create_with_login(self):
        self.client.post(
            self.login_url,
            {"email": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.post(
            self.review_list_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
