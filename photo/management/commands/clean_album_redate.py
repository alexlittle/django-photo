import datetime

from django.core.management.base import BaseCommand
from photo.models import Photo, Album


class Command(BaseCommand):
    help = "Redates photos"

    def add_arguments(self, parser):
        parser.add_argument('date')
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):
        date = options['date'].split('-')
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        new_date = datetime.date(year, month, day)
        album = Album.objects.get(pk=options['album'])
        photos = Photo.objects.filter(album=album)
        for p in photos:
            p.date = new_date
            p.save()
