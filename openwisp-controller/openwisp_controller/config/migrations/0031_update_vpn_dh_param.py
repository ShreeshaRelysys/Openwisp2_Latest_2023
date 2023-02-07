# Generated by Django 3.0.6 on 2020-05-10 07:25

from django.db import migrations

from . import update_vpn_dhparam_length


class Migration(migrations.Migration):

    dependencies = [('config', '0030_django_taggit_update')]

    operations = [
        migrations.RunPython(
            update_vpn_dhparam_length, reverse_code=migrations.RunPython.noop
        )
    ]
