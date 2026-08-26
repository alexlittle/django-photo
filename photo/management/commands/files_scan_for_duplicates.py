import hashlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Photo


class Command(BaseCommand):
    help = "Updates Hash of photos and looks for duplicates"

    def sha512(self, fname):
        hash_sha512 = hashlib.sha512()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha512.update(chunk)
        return hash_sha512.hexdigest()

    def handle(self, *args, **options):
        # create hashes
        to_hash = Photo.objects.filter(file_hash=None)

        for photo in to_hash:
            photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
            if os.path.isfile(photo_path):
                sha512hash = self.sha512(photo_path)
                photo.file_hash = sha512hash
                photo.save()
                print(f"created md5 for {sha512hash}")

        counter = 1
        hashes = Photo.objects.exclude(file_hash=None).values("file_hash").distinct()
        for file_hash in hashes:
            photos = Photo.objects.filter(file_hash=file_hash["file_hash"])
            if photos.count() > 1:
                print("--- " + str(counter) + " ---")
                delete_options = []
                for idx, photo in enumerate(photos):
                    print(
                        "["
                        + str(idx + 1)
                        + "] Duplicate: http://localhost.photo/photo/edit/"
                        + str(photo.id)
                    )
                    print(photo.album.name)
                    delete_option = {"option": idx + 1, "photo": photo.id}
                    delete_options.append(delete_option)
                counter += 1

                select_input = input("Select no to delete: ")
                for option in delete_options:
                    if option["option"] == int(select_input):
                        try:
                            Photo.objects.get(pk=option["photo"]).delete()
                            print("photo deleted")
                        except Photo.DoesNotExist:
                            print("photo not found")
