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
                md5hash = self.md5(photo_path)
                photo.md5hash = md5hash
                photo.save()

        counter = 1
        hashes = Photo.objects.exclude(md5hash=None) \
            .values('md5hash') \
            .distinct()
        for hash in hashes:
            photos = Photo.objects.filter(md5hash=hash['md5hash'])
            if photos.count() > 1:
                print("--- " + str(counter) + " ---")
                delete_options = []
                for idx, photo in enumerate(photos):
                    print("[" + str(idx+1)+"] Duplicate: http://localhost.photo/photo/edit/"
                          + str(photo.id))
                    print( photo.album.name )
                    delete_option = {'option': idx+1,
                                     'photo': photo.id}
                    delete_options.append(delete_option)
                counter += 1
                
                select_input = input("Select no to delete: ")
                for option in delete_options:
                    if option['option'] == int(select_input):
                        try:
                            Photo.objects.get(pk=option['photo']).delete()
                            print("photo deleted")
                        except Photo.DoesNotExist:
                            print("photo not found")
                
