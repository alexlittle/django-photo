
"""
Management command to rewrite exif data
"""

from django.core.management.base import BaseCommand

from photo.models import Photo, Album
from photo.lib import add_or_update_xmp_metadata


class Command(BaseCommand):
    help = "rewrites exif data to photos"

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album ID',
        )

    def handle(self, *args, **options):

        try:
            album = Album.objects.get(id=options['album'])
            print(album.name)
        except Album.DoesNotExist:
            print("Album not found")
            return

        photos = Photo.objects.filter(album=album)
        for photo in photos:
            print(photo)
            add_or_update_xmp_metadata(photo)
