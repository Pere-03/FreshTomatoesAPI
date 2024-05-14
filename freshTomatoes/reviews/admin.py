from django.contrib import admin
from reviews import models


class AuthorAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Review, AuthorAdmin)
