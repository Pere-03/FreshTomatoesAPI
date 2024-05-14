from django.contrib import admin
from users import models


class AuthorAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TomatoeUser, AuthorAdmin)
