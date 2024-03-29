import datetime

from django.core.management.base import BaseCommand
from photo.models import Photo, Tag, PhotoTag


class Command(BaseCommand):
    help = "Checks for photos where date doesn't match"

    def add_arguments(self, parser):
        parser.add_argument('album')

    def handle(self, *args, **options):

        photos = Photo.objects.filter(file__istartswith='img-',
                                      album__pk=options['album'])
        for p in photos:
            print(p.file + " : " + str(p.date))

            year = int(p.file[4:8])
            month = int(p.file[8:10])
            day = int(p.file[10:12])

            if year != p.date.year or \
                    month != p.date.month or \
                    day != p.date.day:
                new_date = datetime.date(year, month, day)
                p.date = new_date
                p.save()

                # add year and month tags
                year = p.date.year
                tag, created = Tag.objects.get_or_create(name=year)
                photo_tag, created = PhotoTag.objects.get_or_create(photo=p, tag=tag)

                month = p.date.strftime("%B")
                tag, created = Tag.objects.get_or_create(name=month)
                photo_tag, created = PhotoTag.objects.get_or_create(photo=p, tag=tag)
