
"""
Management command to find albums with no title set
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Album


class Command(BaseCommand):
    help = "find albums with no title set"

    def handle(self, *args, **options):
        albums = Album.objects.filter(title=None)
        counter = 0
        for a in albums:
            print("%s - %s%s" % (a.name, settings.DOMAIN_NAME, reverse('photo_album', args=(a.id,))))
            counter += 1

        print(counter)
