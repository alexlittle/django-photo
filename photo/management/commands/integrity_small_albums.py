
"""
Management command to find albums with less than X photos
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Album

from . import bcolors


class Command(BaseCommand):
    help = "Finds albums with less than X photos"

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--count',
            dest='max_count',
            help='max_count',
        )

    def handle(self, *args, **options):
        max_count = int(options['max_count'])

        print("Albums with less than %d photos" % max_count)
        print("---------------------------------------")
        counter = 0

        for album in Album.objects.annotate(total=Count("photo")):
            if album.total < max_count:
                print("http://localhost.photo/album/%d - %s - %s [%d photos]"
                      % (album.id, album.title, album.name, album.total))
                counter += 1

        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d albums with less than %d photos %s" % (bcolors.WARNING, counter, max_count, bcolors.ENDC))
        print("---------------------------------------")
