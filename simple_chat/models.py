from django.contrib.auth.models import AbstractUser
from django.forms import ImageField


class User(AbstractUser):
    avatar = ImageField(required=False)
