# Generated by Django 2.1.2 on 2018-11-19 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0012_auto_20181119_2005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='search_name',
            field=models.CharField(blank=True, help_text='the name for this on a CSV to override a general template', max_length=25),
        ),
    ]
