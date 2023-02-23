import datetime

from django.core.management.base import BaseCommand
from photo.models import Photo, Album, PhotoTag, Tag

from . import bcolors

class Command(BaseCommand):
    help = "Retags dates"

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
        
        print("Retagging date tags for %s" % album.title)
        print("---------------------------------------")
        for p in photos:
            print(p)
            # remove existing date tags
            PhotoTag.objects.filter(photo=p, tag__tagcategory__name="Date").delete()
             
            year_tag, created = Tag.objects.get_or_create(name=p.date.year)
            photo_tag, created = PhotoTag.objects.get_or_create(photo=p, tag=year_tag)
            
            month_tag, created = Tag.objects.get_or_create(name=p.date.strftime("%B"))
            photo_tag, created = PhotoTag.objects.get_or_create(photo=p, tag=month_tag)
            print("Added date tags: %s %s" % (year_tag.name, month_tag.name))  
            