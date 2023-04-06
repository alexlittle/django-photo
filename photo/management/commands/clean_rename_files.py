

from django.core.management.base import BaseCommand

from photo.lib import rename_photo_file
from photo.models import Photo, Album


class Command(BaseCommand):
    help = "Rename photos"

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):
        album = Album.objects.get(pk=options['album'])
        photos = Photo.objects.filter(album=album)
        for p in photos:
            rename_photo_file(p)
