
"""
Management command to pre-cache thumbnail images
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Photo


class Command(BaseCommand):
    help = "Pre-caches thumbnail images"

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--size',
            dest='size',
            type=int)

        parser.add_argument(
            '-t',
            '--tag',
            dest='tag',
            help='filter on tag',
        )

    def handle(self, *args, **options):
        if options['size']:
            sizes = [options['size']]
        else:
            sizes = [settings.ALBUM_COVER_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_PDF_SIZE]
            sizes.extend(settings.DEFAULT_THUMBNAIL_SIZES)

        for size in sizes:
            if options['tag']:
                photos = Photo.objects \
                    .filter(phototag__tag__name=options['tag']) \
                    .exclude(thumbnailcache__size=size)
            else:
                photos = Photo.objects.exclude(thumbnailcache__size=size)

            print(str(photos.count()) + " to process")

            for p in photos:
                print("processing: " + p.album.name + p.file)
                thumb_cache = p.get_thumbnail(size)
                if thumb_cache:
                    print(p.get_thumbnail(size))
                else:
                    return
