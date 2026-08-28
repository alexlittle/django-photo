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
        self.hash_unhashed_photos()
        self.review_duplicate_groups()

    def hash_photo(self, photo):
        photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
        if not os.path.isfile(photo_path):
            return

        sha512hash = self.sha512(photo_path)
        photo.file_hash = sha512hash
        photo.save()
        print(f"created hash for {sha512hash}")

    def hash_unhashed_photos(self):
        to_hash = Photo.objects.filter(file_hash="").select_related("album")
        for photo in to_hash:
            self.hash_photo(photo)

    def list_duplicate_group(self, photos):
        """Print each photo in a duplicate group, returning the delete options offered."""
        delete_options = []
        for idx, photo in enumerate(photos):
            link = reverse("photo:edit", args=(photo.id,))
            print(f"[{idx + 1}] Duplicate: {get_domain()}{link}")
            print(photo.album.name)
            delete_options.append({"option": idx + 1, "photo": photo.id})
        return delete_options

    def parse_selection(self, select_input):
        try:
            return int(select_input)
        except ValueError:
            return None

    def delete_selected(self, delete_options, selected):
        for option in delete_options:
            if option["option"] == selected:
                try:
                    Photo.objects.get(pk=option["photo"]).delete()
                    print("photo deleted")
                except Photo.DoesNotExist:
                    print("photo not found")

    def review_duplicate_group(self, counter, photos):
        print("--- " + str(counter) + " ---")
        delete_options = self.list_duplicate_group(photos)

        selected = self.parse_selection(input("Select no to delete: "))
        if selected is not None:
            self.delete_selected(delete_options, selected)

    def review_duplicate_groups(self):
        counter = 1
        hashes = Photo.objects.exclude(file_hash="").values("file_hash").distinct()
        for file_hash in hashes:
            photos = Photo.objects.filter(file_hash=file_hash["file_hash"]).select_related("album")
            if photos.count() > 1:
                self.review_duplicate_group(counter, photos)
                counter += 1
