from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Celebrity(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Rating(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    year = models.IntegerField(
        validators=[MinValueValidator(1895), MaxValueValidator(3000)]
    )
    rating = models.ForeignKey(
        Rating, related_name="movie_rating", on_delete=models.SET_NULL, null=True
    )
    genres = models.ManyToManyField("Genre", related_name="movie_genres", blank=True)
    runtime = models.IntegerField(null=True)
    directors = models.ManyToManyField("Celebrity", related_name="movie_directors")
    cast = models.ManyToManyField("Celebrity", related_name="movie_cast", blank=True)
    poster = models.URLField(null=True)
    userRating = models.DecimalField(
        default=0,
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    votes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.year})"
