from django.contrib import admin
from movies import models


class AuthorAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Movie, AuthorAdmin)
admin.site.register(models.Genre)
admin.site.register(models.Celebrity)
admin.site.register(models.Rating)
