# Generated by Django 4.0.4 on 2022-08-19 11:28

from django.db import migrations

from openwisp_monitoring.check.migrations import (
    assign_check_inline_permissions_to_groups,
)


class Migration(migrations.Migration):

    dependencies = [
        ('sample_check', '0002_check_last_called'),
    ]

    operations = [
        migrations.RunPython(
            assign_check_inline_permissions_to_groups,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
