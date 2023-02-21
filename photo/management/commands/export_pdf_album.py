
"""
Management command to export album
"""
from django.core.management.base import BaseCommand

from photo.export import create_album


class Command(BaseCommand):
    help = "Exports album"

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )
        
        parser.add_argument(
            '-t',
            '--tag',
            dest='tag',
            help='Source Tag',
        )

    def handle(self, *args, **options):
        create_album.make(options['album'], options['tag'])
