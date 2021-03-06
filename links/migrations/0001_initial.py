# Generated by Django 2.1.2 on 2018-11-08 18:01

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('ad_link', 'Ad Link'), ('quick_link', 'Quick Link')], max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
