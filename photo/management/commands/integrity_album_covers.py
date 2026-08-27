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

        self.stdout.write("No cover:")
        self.stdout.write("---------------------------------------")
        counter = 0
        for a in albums:
            if not a.has_cover():
                link = reverse("photo:album", args=(a.id,))
                self.stdout.write(f"{a.name} - {settings.DOMAIN_NAME}{link}")
                counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums without covers"))
        self.stdout.write("---------------------------------------")

        self.stdout.write("Multiple covers:")
        self.stdout.write("---------------------------------------")
        counter = 0
        for a in albums:
            if a.has_multiple_covers():
                link = reverse("photo:album", args=(a.id,))
                self.stdout.write(f"{a.name} - {settings.DOMAIN_NAME}{link}")
                counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums with multiple covers"))
        self.stdout.write("---------------------------------------")
