# Generated by Django 3.2.10 on 2022-01-05 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_squashed_0023_alert_settings_tolerance_remove_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='is_healthy_tolerant',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]