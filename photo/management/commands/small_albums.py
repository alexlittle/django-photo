
"""
Management command to find albums with less than X photos
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Photo, Album


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
        print("Finding albums with less than %d photos" % max_count)
        
        for album in Album.objects.annotate(total=Count("photo")):
            if album.total <= max_count:
                print("http://localhost.photo/album/%d - %s [%d photos]" % (album.id, album.name, album.total))
        
