# Generated by Django 3.1.5 on 2021-01-11 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openwisp_users', '0011_user_first_name_150_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=256, verbose_name='location'),
        ),
    ]
