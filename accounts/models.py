from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [
        ('passenger', "Yo'lovchi"),
        ('driver', 'Haydovchi'),
        ('dispatcher', 'Dispetcher'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='passenger')
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_driver(self):
        return self.role == 'driver'
