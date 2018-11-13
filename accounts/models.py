from django.db import models
from django.contrib.auth.models import AbstractUser
from branchlinks.models import BaseModel


class User(AbstractUser):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True)


class Company(BaseModel):
    name = models.CharField(null=False, max_length=50)

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name
