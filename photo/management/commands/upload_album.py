import glob
import os
import re
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from photo.lib import add_tags, get_exif
from photo.models import Album, Photo, PhotoTag, Tag


class Command(BaseCommand):
    help = "Uploads album to db"

    def add_arguments(self, parser):
        parser.add_argument(
            "-dir",
            "--directory",
            dest="directory",
            help="Source Directory",
        )
        parser.add_argument(
            "-dt",
            "--defaulttags",
            dest="defaulttags",
            help="Default tags",
        )
        parser.add_argument(
            "-dd",
            "--defaultdate",
            dest="defaultdate",
            help="Default date",
        )

    def handle(self, *args, **options):

        directory = options["directory"]
        default_tags = options["defaulttags"]
        default_date = options["defaultdate"]

        # find if dir is already in locations
        album, created = Album.objects.get_or_create(name=directory)

        for img_ext in settings.IMAGE_EXTENSIONS:
            image_files = glob.glob(settings.PHOTO_ROOT + directory + img_ext)
            for im in image_files:
                image_file_name = os.path.basename(im)
                print(image_file_name)
                # find if image exists
                photo, photo_created = Photo.objects.get_or_create(
                    album=album, file=image_file_name
                )

                # add all the tags
                add_tags(photo, default_tags)

                try:
                    exif_tags, result = get_exif(im)
                except AttributeError:  # png files don't generally have exif data
                    result = False

                date_set = False
                if result:
                    try:
                        exif_date = exif_tags["DateTimeOriginal"]
                        naive = parse_datetime(re.sub(r":", r"-", exif_date, count=2))

                        LONDON = ZoneInfo("Europe/London")
                        photo.date = naive.replace(tzinfo=LONDON)
                        date_set = True

                        # add year and month tags
                        year = photo.date.year
                        tag, _ = Tag.objects.get_or_create(name=year)
                        PhotoTag.objects.get_or_create(photo=photo, tag=tag)

                        month = photo.date.strftime("%B")
                        tag, _ = Tag.objects.get_or_create(name=month)
                        PhotoTag.objects.get_or_create(photo=photo, tag=tag)

                    except (KeyError, AttributeError, ValueError):
                        pass

                # PNGs, and JPEGs with no usable EXIF date, fall back to the
                # date typed into the upload form -- but only for photos we're
                # creating now (not ones already on record from an earlier
                # scan), and only when a default was actually supplied (a bare
                # `upload_album` with no -dd leaves the model's own
                # default=timezone.now() in place, same as before).
                if not date_set and photo_created and default_date is not None:
                    photo.date = default_date

                photo.save()

        return str(album.id)
