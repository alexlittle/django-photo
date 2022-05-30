
"""
Management command to pre-cache thumbnail images
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Photo, ThumbnailCache


class Command(BaseCommand):
    help = "Re-caches thumbnail images"

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--size',
            dest='size',
            type=int)

        parser.add_argument(
            '-p',
            '--photo',
            dest='photo',
            help='photo',
        )

    def handle(self, *args, **options):
        if options['size']:
            sizes = [options['size']]
        else:
            sizes = [settings.ALBUM_COVER_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_PDF_SIZE]

        for size in sizes:
            photos = Photo.objects.filter(file=options['photo'])

            print(str(photos.count()) + " to process")

            for p in photos:
                ThumbnailCache.objects.filter(photo=p).delete()
                print("processing: " + p.album.name + p.file)
                thumb_cache = p.get_thumbnail(p, size)
                if thumb_cache:
                    print(p.get_thumbnail(p, size))
                else:
                    return
            
