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

        self.stdout.write("Albums with no title")
        self.stdout.write("---------------------------------------")

        counter = 0
        for a in albums:
            link = reverse("photo:album", args=(a.id,))
            self.stdout.write(f"{a.name} - {settings.DOMAIN_NAME}{link}")
            counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums without a title"))
        self.stdout.write("---------------------------------------")
