import glob
import os
import pytz
import re

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.dateparse import parse_datetime

from photo.models import Album, Photo, Tag, PhotoTag
from photo.lib import get_exif, add_tags


class Command(BaseCommand):
    help = "Uploads album to db"

    def add_arguments(self, parser):
        parser.add_argument(
            '-dir',
            '--directory',
            dest='directory',
            help='Source Directory',
        )
        parser.add_argument(
            '-dt',
            '--defaulttags',
            dest='defaulttags',
            help='Default tags',
        )
        parser.add_argument(
            '-dd',
            '--defaultdate',
            dest='defaultdate',
            help='Default date',
        )

    def handle(self, *args, **options):

        directory = options['directory']
        default_tags = options['defaulttags']
        default_date = options['defaultdate']

        # find if dir is already in locations
        album, created = Album.objects.get_or_create(name=directory)

        for img_ext in settings.IMAGE_EXTENSIONS:
            image_files = glob.glob(settings.PHOTO_ROOT + directory + img_ext)
            for im in image_files:

                image_file_name = os.path.basename(im)
                print(image_file_name)
                # find if image exists
                photo, created = Photo.objects.get_or_create(album=album, file=image_file_name)

                # add all the tags
                add_tags(photo, default_tags)

                try:
                    exif_tags, result = get_exif(im)
                except AttributeError:  # png files don't generally have exif data
                    result = False
                if result:
                    try:
                        exif_date = exif_tags['DateTimeOriginal']
                        naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2))

                        photo.date = pytz.timezone("Europe/London").localize(naive, is_dst=None)

                        # add year and month tags
                        year = photo.date.year
                        tag, created = Tag.objects.get_or_create(name=year)
                        photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)

                        month = photo.date.strftime("%B")
                        tag, created = Tag.objects.get_or_create(name=month)
                        photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)

                    except (KeyError, AttributeError, ValueError):
                        if created:
                            photo.date = default_date

                photo.save()

                # create thumbnails
                for size in settings.DEFAULT_THUMBNAIL_SIZES:
                    photo.get_thumbnail(size)
        return str(album.id)