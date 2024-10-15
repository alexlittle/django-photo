
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
            print("%s - %s%s" % (a.name, settings.DOMAIN_NAME, reverse('photo:album', args=(a.id,))))
            counter += 1

        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d albums without a title%s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")
