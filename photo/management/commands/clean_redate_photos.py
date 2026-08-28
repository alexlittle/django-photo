"""
Management command to redate photos
"""

from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from photo.lib import get_exif
from photo.models import Album, Photo


class Command(BaseCommand):
    help = "Redates photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "-a",
            "--album",
            dest="album",
            help="Source Album",
        )

    def handle(self, *args, **options):
        try:
            album = Album.objects.get(id=options["album"])
        except Album.DoesNotExist:
            print("No Album Specified")
            return

        print("Updating dates for... " + album.name)
        photos = Photo.objects.filter(album=album)

        for photo in photos:
            im = settings.PHOTO_ROOT + album.name + photo.file
            try:
                exif_tags, result = get_exif(im)
            except FileNotFoundError:
                print("File not found: " + photo.file)
                continue
            if result:
                self.update_photo_date(photo, exif_tags)

    def update_photo_date(self, photo, exif_tags):
        try:
            if "DateTimeOriginal" in exif_tags:
                exif_date = exif_tags["DateTimeOriginal"]
            elif "DateTimeDigitized" in exif_tags:
                exif_date = exif_tags["DateTimeDigitized"]
            elif "DateTime" in exif_tags:
                exif_date = exif_tags["DateTime"]
            else:
                raise KeyError("DateTimeOriginal/DateTimeDigitized/DateTime")
            naive = parse_datetime(exif_date.replace(":", "-", 2))
            LONDON = ZoneInfo("Europe/London")
            photo.date = naive.replace(tzinfo=LONDON)
            photo.save()
            print("updated: " + photo.file)
        except KeyError:
            print(exif_tags)
            print("KeyError" + photo.file)
        except AttributeError:
            print("AttributeError " + photo.file)
        except ValueError:
            print("ValueError " + photo.file)
