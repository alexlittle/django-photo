
"""
Management command to find albums with deep directory structure
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Album
from . import bcolors

class Command(BaseCommand):
    help = "Finds albums with deep directory structure"

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--count',
            dest='max_dirs',
            help='max_dirs',
        )

    def handle(self, *args, **options):
        max_dirs = int(options['max_dirs'])
        print("Finds albums deeper than %d directories" % max_dirs)
        print("---------------------------------------")
        counter = 0
        for album in Album.objects.all():
            dirs = filter(None, album.name.split('/'))
            if len(list(dirs)) > max_dirs:
                print("%salbum/%d - %s [%s]" % (settings.DOMAIN_NAME, album.id, album.title, album.name))
                counter += 1
        
        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d directories deeper than%s%s" % (bcolors.WARNING, counter, max_dirs, bcolors.ENDC))
        print("---------------------------------------")
