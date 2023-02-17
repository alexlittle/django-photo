
"""
Management command to find albums with no or multiple covers
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Album


class Command(BaseCommand):
    help = "find albums with no or multiple covers"

    def handle(self, *args, **options):
        albums = Album.objects.all()
        
        print("No cover:")
        print("------------------------")
        counter = 0
        for a in albums:
            if not a.has_cover():
                print("%s - %s%s" % (a.name, settings.DOMAIN_NAME, reverse('photo_album', args=(a.id,))))
                counter += 1
        print(counter)
        
        print("Multiple covers:")
        print("------------------------")
        counter = 0
        for a in albums:
            if a.has_multiple_covers():
                print("%s - %s%s" % (a.name, settings.DOMAIN_NAME, reverse('photo_album', args=(a.id,))))
                counter += 1
        print(counter)
