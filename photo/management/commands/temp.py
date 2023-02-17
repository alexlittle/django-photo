
from django.core.management.base import BaseCommand

from photo.models import Photo, Album, Tag, TagCategory

class Command(BaseCommand):
    help = ""


    def handle(self, *args, **options):
        albums = Album.objects.filter(name__startswith="/negatives/").order_by("-name")
        
        for idx, a in enumerate(albums):
            print("%d http://localhost.photo/album/%d - %s" % (idx, a.id, a.name))