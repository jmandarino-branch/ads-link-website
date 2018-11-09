from django.db import models
from branchlinks.models import BaseModel
from django.contrib.postgres.fields import JSONField

# Create your models here.
LINK_TYPES = (
    ('ad_link', 'Ad Link'),
    ('quick_link', 'Quick Link'),

)


class Link(BaseModel):
    name = models.CharField(null=False, max_length=50)
    type = models.CharField(null=False, choices=LINK_TYPES, max_length=30)
    url = models.CharField(null=True, blank=True, max_length=500)


class LinkDefaults(BaseModel):
    ad_link_dict = JSONField()
    ad_base_url = models.CharField(null=True, blank=True, max_length=25)
    company = models.OneToOneField('accounts.Company', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.company)
