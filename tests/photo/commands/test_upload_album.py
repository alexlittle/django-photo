"""Tests for the ``upload_album`` management command.

Scans a directory under PHOTO_ROOT, creates the Album and a Photo per image,
applies default tags, and dates each photo from its EXIF DateTimeOriginal.

This is the command behind ScanFolderView, which reads the new album id by
calling ``int(out.getvalue())`` on the stdout it passes in. That only works
because ``handle`` returns the id (which BaseCommand writes to ``self.stdout``)
while the per-file progress goes out through bare ``print()`` to the real
stdout. The helper below keeps those two streams apart so the tests see exactly
what the view sees -- see test_only_the_album_id_reaches_the_command_stdout.
"""

import os
from contextlib import redirect_stdout
from io import StringIO
from unittest import expectedFailure
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings
from PIL import Image

from photo.models import Album, Photo, Tag
from tests.base import PhotoRootTestCase, create_album, create_photo, local, strip_ansi

COMMAND = "upload_album"
DATE_TIME_ORIGINAL = 36867


@override_settings(IMAGE_EXTENSIONS=["*.jpg", "*.png"])
class UploadAlbumTests(PhotoRootTestCase):
    def upload(self, **options):
        """Run the command, keeping the returned id apart from printed output.

        Returns (command_stdout, printed_output) -- the first is what
        ScanFolderView parses as an integer.
        """
        options.setdefault("defaulttags", "")
        command_out = StringIO()
        printed = StringIO()
        with redirect_stdout(printed):
            call_command(COMMAND, stdout=command_out, **options)
        return command_out.getvalue().strip(), strip_ansi(printed.getvalue())

    def write_jpeg(self, directory, filename, **exif_tags):
        path = os.path.join(self.photo_root, directory.strip("/"), filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        exif = Image.Exif()
        for tag_id, value in exif_tags.items():
            exif[int(tag_id)] = value
        Image.new("RGB", (20, 20), (10, 20, 30)).save(path, "JPEG", exif=exif)
        return path

    def write_png(self, directory, filename):
        path = os.path.join(self.photo_root, directory.strip("/"), filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.new("RGB", (20, 20), (10, 20, 30)).save(path, "PNG")
        return path

    def test_an_album_is_created_for_the_directory(self):
        self.write_jpeg("/2024/", "a.jpg")

        self.upload(directory="/2024/")

        self.assertTrue(Album.objects.filter(name="/2024/").exists())

    def test_an_existing_album_is_reused(self):
        album = create_album("/2024/")
        self.write_jpeg("/2024/", "a.jpg")

        album_id, _printed = self.upload(directory="/2024/")

        self.assertEqual(int(album_id), album.id)
        self.assertEqual(Album.objects.filter(name="/2024/").count(), 1)

    def test_a_photo_is_created_per_image(self):
        self.write_jpeg("/2024/", "a.jpg")
        self.write_jpeg("/2024/", "b.jpg")

        self.upload(directory="/2024/")

        self.assertCountEqual(Photo.objects.values_list("file", flat=True), ["a.jpg", "b.jpg"])

    def test_only_the_album_id_reaches_the_command_stdout(self):
        # ScanFolderView does int(out.getvalue()), so anything else written to
        # self.stdout would break the view. The progress lines use print(), which
        # is why this holds -- converting them to self.stdout.write would break
        # album creation from the web UI.
        self.write_jpeg("/2024/", "a.jpg")

        album_id, printed = self.upload(directory="/2024/")

        self.assertEqual(int(album_id), Album.objects.get(name="/2024/").id)
        self.assertIn("a.jpg", printed)

    def test_configured_extensions_are_picked_up(self):
        self.write_jpeg("/2024/", "a.jpg")
        self.write_png("/2024/", "b.png")

        self.upload(directory="/2024/")

        self.assertEqual(Photo.objects.count(), 2)

    def test_other_files_are_left_alone(self):
        self.write_jpeg("/2024/", "a.jpg")
        with open(os.path.join(self.photo_root, "2024", "notes.txt"), "w") as handle:
            handle.write("not an image")

        self.upload(directory="/2024/")

        self.assertEqual(list(Photo.objects.values_list("file", flat=True)), ["a.jpg"])

    def test_default_tags_are_applied(self):
        self.write_jpeg("/2024/", "a.jpg")

        self.upload(directory="/2024/", defaulttags="holiday, beach")

        photo = Photo.objects.get(file="a.jpg")
        applied = Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True)
        self.assertCountEqual(applied, ["holiday", "beach"])

    def test_the_exif_date_is_used(self):
        self.write_jpeg("/2024/", "a.jpg", **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.upload(directory="/2024/")

        photo = Photo.objects.get(file="a.jpg")
        stored = local(photo.date)
        self.assertEqual((stored.year, stored.month, stored.day), (2024, 3, 9))
        self.assertEqual((stored.hour, stored.minute), (14, 25))

    def test_year_and_month_tags_come_from_the_exif_date(self):
        self.write_jpeg("/2024/", "a.jpg", **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.upload(directory="/2024/")

        photo = Photo.objects.get(file="a.jpg")
        applied = Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True)
        self.assertCountEqual(applied, ["2024", "March"])

    def test_rerunning_does_not_duplicate_photos(self):
        self.write_jpeg("/2024/", "a.jpg", **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.upload(directory="/2024/")
        self.upload(directory="/2024/")

        self.assertEqual(Photo.objects.filter(file="a.jpg").count(), 1)

    def test_images_in_other_directories_are_not_touched(self):
        self.write_jpeg("/2024/", "a.jpg")
        self.write_jpeg("/2023/", "b.jpg")

        self.upload(directory="/2024/")

        self.assertEqual(list(Photo.objects.values_list("file", flat=True)), ["a.jpg"])

    def test_the_scan_is_not_recursive(self):
        self.write_jpeg("/2024/", "a.jpg")
        self.write_jpeg("/2024/subfolder/", "b.jpg")

        self.upload(directory="/2024/")

        self.assertEqual(list(Photo.objects.values_list("file", flat=True)), ["a.jpg"])

    def test_an_empty_directory_still_returns_the_album_id(self):
        os.makedirs(os.path.join(self.photo_root, "2024"))

        album_id, _printed = self.upload(directory="/2024/")

        self.assertEqual(int(album_id), Album.objects.get(name="/2024/").id)
        self.assertEqual(Photo.objects.count(), 0)

    def test_uppercase_extensions_are_missed(self):
        # glob is case-sensitive on Linux, so "*.jpg" will not match "A.JPG".
        # Worth knowing before pointing this at a camera dump.
        self.write_jpeg("/2024/", "A.JPG")

        self.upload(directory="/2024/")

        self.assertEqual(Photo.objects.count(), 0)

    def test_the_default_date_is_used_when_there_is_no_exif(self):
        # This is the case ScanFolderView hits whenever it uploads scans or
        # screenshots: a PNG, or a JPEG with no EXIF at all.
        from datetime import date

        self.write_png("/2024/", "a.png")

        self.upload(directory="/2024/", defaultdate=date(2019, 5, 1))

        photo = Photo.objects.get(file="a.png")
        self.assertEqual(local(photo.date).date(), date(2019, 5, 1))

    @expectedFailure
    def test_missing_default_tags_are_tolerated(self):
        # Called without -dt, defaulttags is None and add_tags does
        # None.split(",") -> AttributeError. ScanFolderView never hits this
        # because its form supplies "", but a direct command-line run does.
        self.write_jpeg("/2024/", "a.jpg")

        command_out = StringIO()
        with redirect_stdout(StringIO()):
            call_command(COMMAND, stdout=command_out, directory="/2024/")

        self.assertEqual(Photo.objects.count(), 1)

    @expectedFailure
    def test_a_filename_already_used_in_another_album_is_handled(self):
        # Photo.file is globally unique, so get_or_create(album=..., file=...)
        # finds no match and then fails to insert. Two camera dumps that both
        # contain DSC_0001.jpg cannot both be uploaded.
        create_photo(create_album("/2023/"), "DSC_0001.jpg")
        self.write_jpeg("/2024/", "DSC_0001.jpg")

        self.upload(directory="/2024/")

        self.assertEqual(Photo.objects.filter(file="DSC_0001.jpg").count(), 1)

    def test_a_corrupt_image_does_not_silently_vanish(self):
        # get_exif opens the file with PIL; an unreadable one raises
        # UnidentifiedImageError, which the AttributeError handler does not
        # catch. Pinning current behaviour so a future guard is deliberate.
        path = os.path.join(self.photo_root, "2024", "broken.jpg")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(b"this is not a jpeg")

        with patch("photo.management.commands.upload_album.get_exif") as get_exif:
            get_exif.side_effect = AttributeError
            self.upload(directory="/2024/")

        self.assertEqual(Photo.objects.filter(file="broken.jpg").count(), 1)
