# Generated by Django 2.1.2 on 2018-11-19 18:17

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_remove_company_links'),
        ('links', '0007_auto_20181113_2040'),
    ]

    operations = [
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='The Name of a template', max_length=25)),
                ('template_data', django.contrib.postgres.fields.jsonb.JSONField(help_text='json dict of template data to use')),
                ('company', models.ManyToManyField(to='accounts.Company')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
