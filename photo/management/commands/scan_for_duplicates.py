import hashlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from photo.models import Album, Photo


class Command(BaseCommand):
    help = "Updates MD5Hash of photos and looks for duplicates"

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_arguments(self, parser):
        pass
    
    def handle(self, *args, **options):
        # create hashes
        to_hash = Photo.objects.filter(md5hash=None)
        
        for photo in to_hash:
            photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
            if os.path.isfile(photo_path):
                hash = self.md5(photo_path)
                photo.md5hash = hash
                photo.save()
                print(photo_path)
                
        # check for duplicates
        hashes = Photo.objects.exclude(md5hash=None).values('md5hash').distinct()
        for hash in hashes:
            photos = Photo.objects.filter(md5hash=hash['md5hash'])
            if photos.count() > 1:
                for photo in photos:
                    photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
                    print("Duplicate: " + photo_path)
                print("---")
                
                
                
                