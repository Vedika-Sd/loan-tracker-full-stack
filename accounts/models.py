
# Create your models here.
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        OFFICER = 'officer', 'Officer'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)

    def is_officer(self):
        return self.role == self.Role.OFFICER
