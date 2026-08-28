import hashlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.lib import get_domain
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
        to_hash = Photo.objects.filter(file_hash="").select_related("album")

        for photo in to_hash:
            photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
            if os.path.isfile(photo_path):
                sha512hash = self.sha512(photo_path)
                photo.file_hash = sha512hash
                photo.save()
                print(f"created hash for {sha512hash}")

        counter = 1
        hashes = Photo.objects.exclude(file_hash="").values("file_hash").distinct()
        for file_hash in hashes:
            photos = Photo.objects.filter(file_hash=file_hash["file_hash"]).select_related("album")
            if photos.count() > 1:
                print("--- " + str(counter) + " ---")
                delete_options = []
                for idx, photo in enumerate(photos):
                    link = reverse("photo:edit", args=(photo.id,))
                    print(f"[{idx + 1}] Duplicate: {get_domain()}{link}")
                    print(photo.album.name)
                    delete_option = {"option": idx + 1, "photo": photo.id}
                    delete_options.append(delete_option)
                counter += 1

                select_input = input("Select no to delete: ")
                try:
                    selected = int(select_input)
                except ValueError:
                    selected = None

                if selected is not None:
                    for option in delete_options:
                        if option["option"] == selected:
                            try:
                                Photo.objects.get(pk=option["photo"]).delete()
                                print("photo deleted")
                            except Photo.DoesNotExist:
                                print("photo not found")
