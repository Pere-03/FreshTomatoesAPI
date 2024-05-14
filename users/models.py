from django.db import models
from django.contrib.auth.models import AbstractUser


class TomatoeUser(AbstractUser):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    tel = models.CharField(max_length=32)
    email = models.EmailField(max_length=128)
    password = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
