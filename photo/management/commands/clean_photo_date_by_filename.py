
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
        year = date[0]
        month = date[1]
        day = date[2]
        album = Album.objects.get(pk=options['album'])
        photos = Photo.objects.filter(
            date__year=year, date__month=month, date__day=day, album=album)

        for photo in photos:
            new_year = int(photo.file[4:8])
            new_month = int(photo.file[8:10])
            new_day = int(photo.file[10:12])
            new_date = datetime.date(new_year, new_month, new_day)
            print(new_date)
            photo.date = new_date
            photo.save()
