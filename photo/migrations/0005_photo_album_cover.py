# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-19 13:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0004_auto_20171119_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='album_cover',
            field=models.BooleanField(default=False),
        ),
    ]
