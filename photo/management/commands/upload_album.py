import glob
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from photo.lib import add_tags, get_exif
from photo.models import Album, Photo, PhotoTag, Tag

LONDON = ZoneInfo("Europe/London")


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
        album, _ = Album.objects.get_or_create(name=directory)

        for img_ext in settings.IMAGE_EXTENSIONS:
            for im in glob.glob(settings.PHOTO_ROOT + directory + img_ext):
                self.upload_photo(im, album, default_tags, default_date)

        return str(album.id)

    def upload_photo(self, im, album, default_tags, default_date):
        image_file_name = os.path.basename(im)
        print(image_file_name)
        # Photo.file is globally unique, so look it up by file alone -- a
        # filename already used in another album stays there rather than
        # duplicating or erroring.
        photo, photo_created = Photo.objects.get_or_create(
            file=image_file_name, defaults={"album": album}
        )

        # add all the tags
        add_tags(photo, default_tags)

        date_set = self.set_exif_date(photo, im)

        # PNGs, and JPEGs with no usable EXIF date, fall back to the date
        # typed into the upload form -- but only for photos we're creating
        # now (not ones already on record from an earlier scan), and only
        # when a default was actually supplied (a bare `upload_album` with
        # no -dd leaves the model's own default=timezone.now() in place,
        # same as before).
        if not date_set and photo_created and default_date is not None:
            photo.date = timezone.make_aware(datetime.combine(default_date, time.min))

        photo.save()

    def set_exif_date(self, photo, im):
        try:
            exif_tags, result = get_exif(im)
        except AttributeError:  # png files don't generally have exif data
            return False

        if not result:
            return False

        try:
            exif_date = exif_tags["DateTimeOriginal"]
            naive = parse_datetime(exif_date.replace(":", "-", 2))
            photo.date = naive.replace(tzinfo=LONDON)

            # add year and month tags
            year_tag, _ = Tag.objects.get_or_create(name=photo.date.year)
            PhotoTag.objects.get_or_create(photo=photo, tag=year_tag)

            month_tag, _ = Tag.objects.get_or_create(name=photo.date.strftime("%B"))
            PhotoTag.objects.get_or_create(photo=photo, tag=month_tag)
        except (KeyError, AttributeError, ValueError):
            return False

        return True
