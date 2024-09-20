import os

from shutil import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Photo, Tag


class Command(BaseCommand):
    help = "Exports tag photos"

    def add_arguments(self, parser):
        parser.add_argument('tag')
        parser.add_argument('export_path', nargs='?')

    def handle(self, *args, **options):
        slug_list = options['tag'].split('+')
        photos = Photo.objects.filter(phototag__tag__slug__in=slug_list) \
            .annotate(count=Count('id')) \
            .filter(count=len(slug_list))

        if not options['export_path']:
            export_path = os.path.join(settings.PHOTO_ROOT, 'export', options['tag'])
            try:
                os.makedirs(export_path)
            except OSError:
                print("couldn't create directory - maybe it already exists?")
        else:
            export_path = options['export_path']

        for photo in photos:
            file_to_copy = os.path.join(settings.PHOTO_ROOT,
                                        photo.album.name[1:],
                                        photo.file)
            copy(file_to_copy, export_path)
