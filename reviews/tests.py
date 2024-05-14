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
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.post(
            self.review_list_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestReviewFiltering(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.review_list_url = reverse("review_list")
        self.user1 = TomatoeUser.objects.create_user(
            username="testuser1@test.com",
            name="Test User 1",
            tel="123456789",
            email="testuser1@test.com",
            password="Testpassword1",
        )
        self.user2 = TomatoeUser.objects.create_user(
            username="testuser2@test.com",
            name="Test User 2",
            tel="123456789",
            email="testuser2@test.com",
            password="Testpassword1",
        )
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.movie1 = Movie.objects.create(
            title="Test Movie 1",
            year=2020,
            rating=self.rating,
            runtime=120,
            userRating=7.5,
            votes=1000,
        )
        self.movie2 = Movie.objects.create(
            title="Test Movie 2",
            year=2021,
            rating=self.rating,
            runtime=130,
            userRating=8.0,
            votes=2000,
        )
        self.review1 = Review.objects.create(
            user=self.user1, movie=self.movie1, userRating=8.0, comment="Great movie!"
        )
        self.review2 = Review.objects.create(
            user=self.user2, movie=self.movie2, userRating=9.0, comment="Awesome movie!"
        )

    def test_review_filtering_by_user(self):
        response = self.client.get(
            self.review_list_url, {"user_id": self.user1.id}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user"]["id"], self.user1.id)

    def test_review_filtering_by_movie(self):
        response = self.client.get(
            self.review_list_url, {"movie_id": self.movie1.id}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["movie"]["id"], self.movie1.id)

    def test_review_filtering_by_movie_title(self):
        response = self.client.get(
            self.review_list_url, {"title": "Test Movie 1"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["movie"]["id"], self.movie1.id)

    def test_review_ordering_by_userRating(self):
        response = self.client.get(
            self.review_list_url, {"ordering": "userRating"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["userRating"], self.review1.userRating)
        self.assertEqual(data[1]["userRating"], self.review2.userRating)

        response = self.client.get(
            self.review_list_url, {"ordering": "-userRating"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["userRating"], self.review2.userRating)
        self.assertEqual(data[1]["userRating"], self.review1.userRating)


class TestReviewDetailView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
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
            movie=self.movie,
            user=self.user,
            userRating=8.0,
            comment="Great movie!",
        )
        self.review_detail_url = reverse("review_detail", kwargs={"pk": self.review.id})
        self.review_data = {
            "userRating": 9.0,
            "comment": "Updated comment!",
        }
        self.user2 = TomatoeUser.objects.create_user(
            username="testuser2@test.com",
            name="Test User 2",
            tel="123456789",
            email="testuser2@test.com",
            password="Testpassword2",
        )
        self.movie2 = Movie.objects.create(
            title="Test Movie 2",
            year=2021,
            rating=self.rating,
            runtime=130,
            userRating=8.0,
            votes=2000,
        )
        self.bad_review_data = {
            "movie": self.movie2.id,
            "userRating": 9.0,
            "comment": "Updated comment!",
        }

    def test_review_update_without_login(self):
        response = self.client.put(
            self.review_detail_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_update_with_login(self):
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.put(
            self.review_detail_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_review_partial_update_without_login(self):
        response = self.client.patch(
            self.review_detail_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_partial_update_with_login(self):
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.patch(
            self.review_detail_url, self.review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_review_delete_without_login(self):
        response = self.client.delete(self.review_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_delete_with_login(self):
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.delete(self.review_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_review_delete_by_different_user(self):
        self.client.post(
            self.login_url,
            {"username": "testuser2@test.com", "password": "Testpassword2"},
            format="json",
        )
        response = self.client.delete(self.review_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_update_same_user_different_movie(self):
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )

        response = self.client.put(
            self.review_detail_url, self.bad_review_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_partial_update_same_user_different_movie(self):
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.patch(
            self.review_detail_url, {"movie": self.bad_review_data["movie"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
