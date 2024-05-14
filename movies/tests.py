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
        self.movie_detail_url = reverse(
            "movie_detail", kwargs={"movie_pk": self.movie.id}
        )

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
            {"email": "testuser@test.com", "password": "Testpassword1"},
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
            {"email": "testuser@test.com", "password": "Testpassword1"},
            format="json",
        )
        response = self.client.post(self.movie_list_url, self.movie_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestMovieCreateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.movie_list_url = reverse('movie_list')
        self.genre = Genre.objects.create(name="Action")
        self.celebrity = Celebrity.objects.create(name="Test Celebrity")
        self.rating = Rating.objects.create(name="PG-13")
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            password="Testpassword1",
            is_staff=True
        )
        self.client.post(self.login_url, {'email': 'testuser@test.com', 'password': 'Testpassword1'}, format='json')

    def test_movie_create_without_title(self):
        movie_data = {
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id]
        }
        response = self.client.post(self.movie_list_url, movie_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_movie_create_without_director(self):
        movie_data = {
            "title": "Test Movie",
            "year": 2020,
            "rating": self.rating.id,
            "runtime": 120,
            "userRating": 7.5,
            "votes": 1000,
            "cast": [self.celebrity.id]
        }
        response = self.client.post(self.movie_list_url, movie_data, format='json')
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
            "poster": "invalid_url"
        }
        response = self.client.post(self.movie_list_url, movie_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMovieFiltering(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.movie_list_url = reverse('movie_list')
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            password="Testpassword1",
            is_staff=True
        )
        self.client.post(self.login_url, {'email': 'testuser@test.com', 'password': 'Testpassword1'}, format='json')
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

    def test_movie_filtering(self):
        response = self.client.get(self.movie_list_url, {'title': 'Test Movie'}, format='json')
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Movie')

        response = self.client.get(self.movie_list_url, {'genre': 'Action'}, format='json')
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['genres'][0], 'Action')

        response = self.client.get(self.movie_list_url, {'director': 'Test Celebrity'}, format='json')
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['directors'][0], 'Test Celebrity')

        response = self.client.get(self.movie_list_url, {'rating': 'PG-13'}, format='json')
        data = response.data["results"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['rating'], 'PG-13')


class TestMovieUpdateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user = TomatoeUser.objects.create_user(
            username="testuser@test.com",
            password="Testpassword1",
            is_staff=True
        )
        self.client.post(self.login_url, {'email': 'testuser@test.com', 'password': 'Testpassword1'}, format='json')
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
        self.movie_detail_url = reverse('movie_detail', kwargs={'movie_pk': self.movie.id})

    def test_movie_update_with_staff_user(self):
        movie_data = {
            "title": "Updated Movie",
            "year": 2021,
            "rating": self.rating.id,
            "runtime": 130,
            "userRating": 8.0,
            "votes": 2000,
            "genres": [self.genre.id],
            "directors": [self.celebrity.id],
            "cast": [self.celebrity.id]
        }
        response = self.client.put(self.movie_detail_url, movie_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Movie')
