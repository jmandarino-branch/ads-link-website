# Generated by Django 2.1.2 on 2018-11-08 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20181108_1806'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name_plural': 'Companies'},
        ),
        migrations.AlterField(
            model_name='company',
            name='links',
            field=models.ManyToManyField(to='links.Link'),
        ),
    ]
