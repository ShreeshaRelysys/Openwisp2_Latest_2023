# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-01 17:00
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='BoxedLocation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=32)),
                ('slug', models.SlugField(blank=True, max_length=128, unique=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                (
                    'geometry',
                    django.contrib.gis.db.models.fields.GeometryField(srid=4326),
                ),
                (
                    'bbox_geometry',
                    django.contrib.gis.db.models.fields.PolygonField(srid=4326),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='LocatedFile',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=32)),
                ('slug', models.SlugField(blank=True, max_length=128, unique=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                (
                    'geometry',
                    django.contrib.gis.db.models.fields.GeometryField(srid=4326),
                ),
                (
                    'file',
                    models.FileField(blank=True, null=True, upload_to='located_files'),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=32)),
                ('slug', models.SlugField(blank=True, max_length=128, unique=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                (
                    'geometry',
                    django.contrib.gis.db.models.fields.GeometryField(srid=4326),
                ),
            ],
            options={'abstract': False},
        ),
    ]