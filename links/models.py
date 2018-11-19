from django.db import models
from branchlinks.models import BaseModel
from django.contrib.postgres.fields import JSONField

# Create your models here.
LINK_TYPES = (
    ('ad_link', 'Ad Link'),
    ('quick_link', 'Quick Link'),

)

TEMPLATE_TYPE = (

    ('ad', 'Advertment Link'),
)


class Link(BaseModel):
    name = models.CharField(null=False, max_length=50)
    type = models.CharField(null=False, choices=LINK_TYPES, max_length=30)
    url = models.CharField(null=True, blank=True, max_length=500)


class LinkDefault(BaseModel):
    ad_link_dict = JSONField(help_text='make sure "base_url" is included in the json dict')
    ad_base_url = models.CharField(null=True, blank=True, max_length=25)
    company = models.OneToOneField('accounts.Company', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.company)


class Template(BaseModel):
    name = models.CharField(max_length=25, help_text='The Name of a template')
    company = models.ManyToManyField('accounts.Company', related_name='templates',
                                     help_text='The companies who can view this')
    template_data = JSONField(help_text='json dict of template data to use')
    type = models.CharField(choices=TEMPLATE_TYPE, max_length=15,
                            help_text='The type of link this template is associated with')
    search_name = models.CharField(max_length=25, blank=True,
                                   help_text='the name for this on a CSV to override a general template')

    def __str__(self):
        return self.name

