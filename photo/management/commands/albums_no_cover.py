
"""
Management command to find albums with no cover set
"""

from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Album


class Command(BaseCommand):
    help = "find albums with no cover set"

    def handle(self, *args, **options):
        albums = Album.objects.all()
        counter = 0
        for a in albums:
            if not a.has_cover():
                print(a.name + " - http://localhost.photo" +
                      reverse('photo_album', args=(a.id,)))
                counter += 1

        print(counter)
