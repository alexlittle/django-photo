"""
Management command to find albums with no title set
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Album

from . import bcolors


class Command(BaseCommand):
    help = "find albums with no title set"

    def handle(self, *args, **options):
        albums = Album.objects.filter(title=None)

        print("Albums with no title")
        print("---------------------------------------")

        counter = 0
        for a in albums:
            link = reverse("photo:album", args=(a.id,))
            print(f"{a.name} - {settings.DOMAIN_NAME}{link}")
            counter += 1

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} albums without a title{bcolors.ENDC}")
        print("---------------------------------------")
