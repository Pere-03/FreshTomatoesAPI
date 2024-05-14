from django.db import models
from users.models import TomatoeUser
from movies.models import Movie
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TomatoeUser, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    userRating = models.DecimalField(
        default=0,
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.movie.title}"
