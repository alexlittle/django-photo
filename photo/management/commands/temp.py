
from django.core.management.base import BaseCommand
from django.conf import settings

from photo.models import Photo, Album, Tag, TagCategory
from . import bcolors

class Command(BaseCommand):
    help = ""


    def handle(self, *args, **options):
        albums = Album.objects.filter(id__in=[1155,1202]).order_by('name')
        
        for a in albums:
            print("%s%s/album/%d - %s%s" % (bcolors.OK, settings.DOMAIN_NAME, a.id, a.name, bcolors.ENDC))
            photos = Photo.objects.filter(album=a).order_by('id')
            for idx, p in enumerate(photos):
                if idx % 10 == 0:
                    print("----------------------------------------------")
                print("%d %s%s - %sphoto/edit/%d" % (idx, a.name, p.file, settings.DOMAIN_NAME, p.id))
                print("-")