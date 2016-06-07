from django.db import models

from django.contrib.auth.models import AbstractUser


__all__ = [ 'User' ]


class User(AbstractUser):

    biography = models.TextField(blank=True, verbose_name='Biography')
