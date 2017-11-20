# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-20 17:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import photo.cache_storage
import photo.models


class Migration(migrations.Migration):

    replaces = [(b'photo', '0001_initial'), (b'photo', '0002_location_title'), (b'photo', '0003_auto_20171119_1041'), (b'photo', '0004_auto_20171119_1139'), (b'photo', '0005_photo_album_cover'), (b'photo', '0006_thumbnailcache'), (b'photo', '0007_auto_20171120_1250'), (b'photo', '0008_auto_20171120_1448'), (b'photo', '0009_auto_20171120_1527'), (b'photo', '0010_auto_20171120_1712')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.TextField()),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photo.Location')),
            ],
        ),
        migrations.CreateModel(
            name='PhotoTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photo.Photo')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='phototag',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photo.Tag'),
        ),
        migrations.AddField(
            model_name='location',
            name='title',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='location',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='photo',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RenameModel(
            old_name='Location',
            new_name='Album',
        ),
        migrations.RenameField(
            model_name='photo',
            old_name='location',
            new_name='album',
        ),
        migrations.AddField(
            model_name='photo',
            name='album_cover',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='ThumbnailCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.IntegerField()),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to=photo.models.image_file_name)),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photo.Photo')),
            ],
            options={
                'verbose_name': 'Thumbnail Cache',
                'verbose_name_plural': 'Thumbnail Caches',
            },
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orig_file', models.ImageField(storage=photo.cache_storage.ImageCacheFileSystemStorage(), upload_to=photo.cache_storage.media_file_name)),
                ('md5sum', models.CharField(max_length=36)),
            ],
        ),
        migrations.CreateModel(
            name='TagCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Tag Category',
                'verbose_name_plural': 'Tag Categories',
            },
        ),
        migrations.AddField(
            model_name='tag',
            name='tagcategory',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='photo.TagCategory'),
        ),
        migrations.AlterModelOptions(
            name='album',
            options={'verbose_name': 'Album', 'verbose_name_plural': 'Album'},
        ),
        migrations.AlterModelOptions(
            name='photo',
            options={'verbose_name': 'Photo', 'verbose_name_plural': 'Photos'},
        ),
        migrations.AlterModelOptions(
            name='phototag',
            options={'verbose_name': 'Photo Tag', 'verbose_name_plural': 'Photo Tags'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'Tag', 'verbose_name_plural': 'Tags'},
        ),
    ]
