"""
Management command to find albums with no or multiple covers
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Album

from . import bcolors


class Command(BaseCommand):
    help = "find albums with no or multiple covers"

    def handle(self, *args, **options):
        albums = Album.objects.all()

        print("No cover:")
        print("---------------------------------------")
        counter = 0
        for a in albums:
            if not a.has_cover():
                link = reverse("photo:album", args=(a.id,))
                print(f"{a.name} - {settings.DOMAIN_NAME}{link}")
                counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} albums without covers{bcolors.ENDC}")
        print("---------------------------------------")

        print("Multiple covers:")
        print("---------------------------------------")
        counter = 0
        for a in albums:
            if a.has_multiple_covers():
                link = reverse("photo:album", args=(a.id,))
                print(f"{a.name} - {settings.DOMAIN_NAME}{link}")
                counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} albums with multiple covers{bcolors.ENDC}")
        print("---------------------------------------")
