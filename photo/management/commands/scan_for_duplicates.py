import hashlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Photo


class Command(BaseCommand):
    help = "Updates MD5Hash of photos and looks for duplicates"

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def handle(self, *args, **options):
        # create hashes
        to_hash = Photo.objects.filter(md5hash=None)

        for photo in to_hash:
            photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
            if os.path.isfile(photo_path):
                hash = self.md5(photo_path)
                photo.md5hash = hash
                photo.save()

        counter = 1
        hashes = Photo.objects.exclude(md5hash=None) \
            .values('md5hash') \
            .distinct()
        for hash in hashes:
            photos = Photo.objects.filter(md5hash=hash['md5hash'])
            if photos.count() > 1:
                print("--- " + str(counter) + " ---")
                for photo in photos:
                    print("Duplicate: http://localhost.photo/photo/edit/"
                          + str(photo.id))
                counter += 1
