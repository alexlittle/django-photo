
"""
Management command to pre-cache thumbnail images
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Photo, ThumbnailCache

from . import bcolors


class Command(BaseCommand):
    help = "Pre-caches thumbnail images"

    def add_arguments(self, parser):
        parser.add_argument('-s', '--size', dest='size', type=int)
        parser.add_argument('-t', '--tag', dest='tag', help='filter on tag')
        parser.add_argument('-a', '--album', dest='album', help='Source Album ID', type=int)
        parser.add_argument('-o', '--overwrite', dest='overwrite', default=False, type=bool)

    def handle(self, *args, **options):
        if options['size']:
            sizes = [options['size']]
        else:
            sizes = [settings.ALBUM_COVER_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_THUMBNAIL_SIZE,
                     settings.PHOTO_DEFAULT_PDF_SIZE]
            sizes.extend(settings.DEFAULT_THUMBNAIL_SIZES)
            # remove duplicates
            sizes = list(set(sizes))

        for i, size in enumerate(sizes):
            if options['tag']:
                photos = Photo.objects.filter(phototag__tag__name=options['tag'])
            elif options['album']:
                photos = Photo.objects.filter(album__id=options['album'])
            else:
                photos = Photo.objects.all()

            if not options['overwrite']:
                # exclude existing thumbnail cache files
                photos = photos.exclude(thumbnailcache__size=size)

            print(str(photos.count()) + " to process")

            for j, p in enumerate(photos):
                print("%s(size %d/%d) %d/%d Processing: %s%s%s" % (bcolors.OK,
                                                                   i+1,
                                                                   len(sizes),
                                                                   j+1,
                                                                   photos.count(),
                                                                   p.album.name,
                                                                   p.file,
                                                                   bcolors.ENDC))
                if options['overwrite']:
                    # remove existing thumbnail cache object first
                    ThumbnailCache.objects.filter(size=size, photo=p).delete()
                thumb_cache = p.get_thumbnail(size)
                if thumb_cache:
                    print(p.get_thumbnail(size))
                else:
                    return
