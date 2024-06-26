from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from movies.models import Movie, Genre, Celebrity, Rating
from users.models import TomatoeUser


class TestMovieModel(TestCase):
    def setUp(self):
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

    def test_movie_creation(self):
        self.assertEqual(Movie.objects.count(), 1)


class TestMovieListView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.movie_list_url = reverse("movie_list")

    def test_movie_list(self):
        response = self.client.get(self.movie_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_movie_list_with_filters(self):
        response = self.client.get(self.movie_list_url, {"title": "Test Movie"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestMovieDetailView(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        self.movie_detail_url = reverse("movie_detail", kwargs={"pk": self.movie.id})

    def test_movie_detail(self):
        response = self.client.get(self.movie_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestMovieUserCreateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.movie_list_url = reverse("movie_list")
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.movie_data = {
            "title": "Test Movie",
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id],
        }

    def test_movie_create_without_login(self):
        response = self.client.post(self.movie_list_url, self.movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_movie_create_with_non_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=False
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.post(self.movie_list_url, self.movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_movie_create_with_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.post(self.movie_list_url, self.movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestMovieCreateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.movie_list_url = reverse("movie_list")
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )

    def test_movie_create_without_title(self):
        movie_data = {
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id],
        }
        response = self.client.post(self.movie_list_url, movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_movie_create_without_director(self):
        movie_data = {
            "title": "Test Movie",
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "cast": [self.celebrity.id],
        }
        response = self.client.post(self.movie_list_url, movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_movie_create_with_invalid_url(self):
        movie_data = {
            "title": "Test Movie",
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id],
            "poster": "invalid_url",
        }
        response = self.client.post(self.movie_list_url, movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMovieFiltering(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.movie_list_url = reverse("movie_list")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        self.genre = Genre.objects.create(name="Romance")
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

        self.genre2 = Genre.objects.create(name="Action")
        self.rating2 = Rating.objects.create(name="R")
        self.movie2 = Movie.objects.create(
            title="Bad movie",
            year=2021,
            rating=self.rating2,
            runtime=130,
            userRating=8.0,
            votes=2000,
        )
        self.movie2.genres.add(self.genre2)

    def test_movie_filtering(self):
        response = self.client.get(
            self.movie_list_url, {"search": "Test Movie"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test Movie")

        response = self.client.get(
            self.movie_list_url, {"genres": "Action"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        movie = Movie.objects.get(id=data[0]["id"])
        genres = [genre.name for genre in movie.genres.all()]
        self.assertIn("Action", genres)

        response = self.client.get(
            self.movie_list_url, {"search": "Test Celebrity"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        movie = Movie.objects.get(id=data[0]["id"])
        directors = [director.name for director in movie.directors.all()]
        self.assertIn("Test Celebrity", directors)

        response = self.client.get(
            self.movie_list_url, {"rating": "PG-13"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        movie = Movie.objects.get(id=data[0]["id"])
        rating = movie.rating.name
        self.assertEqual(rating, "PG-13")

    def test_movie_ordering(self):
        self.movie3 = Movie.objects.create(
            title="Test Movie 3",
            year=2019,
            rating=self.rating,
            runtime=110,
            userRating=6.5,
            votes=1500,
        )

        response = self.client.get(
            self.movie_list_url, {"ordering": "year"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["year"], self.movie3.year)
        self.assertEqual(data[1]["year"], self.movie.year)
        self.assertEqual(data[2]["year"], self.movie2.year)

        response = self.client.get(
            self.movie_list_url, {"ordering": "-userRating"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["userRating"], self.movie2.userRating)
        self.assertEqual(data[1]["userRating"], self.movie.userRating)
        self.assertEqual(data[2]["userRating"], self.movie3.userRating)

        response = self.client.get(
            self.movie_list_url, {"ordering": "runtime"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["runtime"], self.movie3.runtime)
        self.assertEqual(data[1]["runtime"], self.movie.runtime)
        self.assertEqual(data[2]["runtime"], self.movie2.runtime)

        response = self.client.get(
            self.movie_list_url, {"ordering": "-votes"}, format="json"
        )
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["votes"], self.movie2.votes)
        self.assertEqual(data[1]["votes"], self.movie3.votes)
        self.assertEqual(data[2]["votes"], self.movie.votes)


class TestMovieUpdateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
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
        self.movie_detail_url = reverse("movie_detail", kwargs={"pk": self.movie.id})
        self.movie_data = {
            "title": "Updated Movie",
            "year": 2021,
            "rating": self.rating.id,
            "runtime": 130,
            "userRating": 8.0,
            "votes": 2000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id],
        }

    def test_movie_update_without_login(self):
        response = self.client.put(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_movie_update_with_non_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=False
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.put(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_movie_update_with_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.put(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_movie_delete_without_login(self):
        response = self.client.delete(self.movie_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_movie_delete_with_non_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=False
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.delete(self.movie_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_movie_delete_with_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.delete(self.movie_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_movie_partial_update_without_login(self):
        response = self.client.patch(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_movie_partial_update_with_non_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=False
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.patch(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_movie_partial_update_with_staff_user(self):
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com", password="Testpassword1", is_staff=True
        )
        self.client.post(
            self.login_url,
            {"username": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.patch(
            self.movie_detail_url, self.movie_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
