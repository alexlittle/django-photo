"""Tests for the ``files_scan_photos`` management command.

Two independent passes, requiring at least one of the two flags that select
them:
  --files  walks PHOTO_ROOT and reports images with no database row
  --db     walks the database and reports rows with no file on disk
"""

import os

from django.core.management.base import CommandError
from django.test import override_settings

from photo.models import Photo
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "files_scan_photos"


@override_settings(IGNORE_FOLDERS=[], IGNORE_EXTENSIONS=[".db", ".ini"])
class FilesScanPhotosNoFlagsTests(CommandTestCase):
    def test_without_flags_the_command_errors(self):
        album = create_album("/2024/")
        create_photo(album, "orphan.jpg")

        with self.assertRaises(CommandError):
            self.run_command(COMMAND)

    def test_autoadd_is_no_longer_a_recognised_option(self):
        # The dead --autoadd flag (declared but never read in handle()) has
        # been removed rather than implemented.
        album = create_album("/2024/")
        photo = create_photo(album, "a.jpg")
        self.write_image(photo)

        with self.assertRaises(TypeError):
            self.run_command(COMMAND, files=True, autoadd=True)

    def touch(self, album_name, filename):
        directory = os.path.join(self.photo_root, album_name.lstrip("/"))
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)
        with open(path, "wb") as handle:
            handle.write(b"not really an image")
        return path


@override_settings(IGNORE_FOLDERS=[], IGNORE_EXTENSIONS=[".db", ".ini"])
class FilesScanPhotosFilesPassTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def touch(self, filename, album_name="/2024/"):
        directory = os.path.join(self.photo_root, album_name.lstrip("/"))
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)
        with open(path, "wb") as handle:
            handle.write(b"not really an image")
        return path

    def test_reports_a_file_with_no_database_row(self):
        self.touch("orphan.jpg")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("/2024/orphan.jpg", output)
        self.assertIn("notfound", output)
        self.assertIn("1 photos not in database", output)

    def test_a_file_with_a_row_is_not_reported(self):
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, files=True)

        self.assertNotIn("notfound", output)
        self.assertIn("OK", output)

    def test_verbose_lists_the_files_that_were_found(self):
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, files=True, verbose=True)

        self.assertIn("/2024/known.jpg found", output)

    def test_non_verbose_stays_quiet_about_files_that_were_found(self):
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, files=True)

        self.assertNotIn("known.jpg found", output)

    def test_counts_every_missing_file(self):
        self.touch("one.jpg")
        self.touch("two.jpg")
        self.touch("three.jpg", album_name="/2023/")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("3 photos not in database", output)

    def test_ignored_extensions_are_skipped(self):
        self.touch("real.jpg")
        self.touch("Thumbs.db")
        self.touch("desktop.ini")

        output = self.run_command(COMMAND, files=True)

        self.assertNotIn("Thumbs.db", output)
        self.assertNotIn("desktop.ini", output)

    def test_ignored_folders_are_skipped(self):
        self.touch("hidden.jpg", album_name="/.thumbnails/")
        self.touch("visible.jpg")

        with override_settings(IGNORE_FOLDERS=[r".*\.thumbnails.*"]):
            output = self.run_command(COMMAND, files=True)

        self.assertNotIn("hidden.jpg", output)
        self.assertIn("visible.jpg", output)

    def test_a_file_in_an_album_that_does_not_exist_is_reported(self):
        self.touch("stray.jpg", album_name="/1999/")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("/1999/stray.jpg", output)

    def test_duplicate_detection_reports_ok(self):
        # Photo.file is unique=True at the model level, so a photo can never
        # have more than one database entry -- this section always reports OK.
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, files=True)

        self.assertIn("Multiple copies of photo in database", output)

    def test_a_scan_that_examines_no_files_does_not_crash(self):
        # A folder holding nothing but Thumbs.db means the inner `for name in
        # files` loop body never runs, on an empty PHOTO_ROOT and on any tree
        # where every file is filtered out by IGNORE_EXTENSIONS.
        self.touch("Thumbs.db")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("OK", output)


@override_settings(IGNORE_FOLDERS=[], IGNORE_EXTENSIONS=[".db", ".ini"])
class FilesScanPhotosDbPassTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_reports_a_row_with_no_file(self):
        create_photo(self.album, "ghost.jpg")

        output = self.run_command(COMMAND, db=True)

        self.assertIn("/2024/ghost.jpg not found", output)
        self.assertIn("1 photos in database but not on file", output)

    def test_a_row_with_a_file_is_not_reported(self):
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, db=True)

        self.assertNotIn("not found", output)
        self.assertIn("OK", output)

    def test_verbose_lists_the_rows_that_were_found(self):
        photo = create_photo(self.album, "known.jpg")
        self.write_image(photo)

        output = self.run_command(COMMAND, db=True, verbose=True)

        self.assertIn("/2024/known.jpg found", output)

    def test_autodelete_removes_rows_with_no_file(self):
        create_photo(self.album, "ghost.jpg")
        kept = create_photo(self.album, "known.jpg")
        self.write_image(kept)

        output = self.run_command(COMMAND, db=True, autodelete=True)

        self.assertFalse(Photo.objects.filter(file="ghost.jpg").exists())
        self.assertTrue(Photo.objects.filter(file="known.jpg").exists())
        self.assertIn("... DELETED", output)

    def test_without_autodelete_nothing_is_removed(self):
        create_photo(self.album, "ghost.jpg")

        self.run_command(COMMAND, db=True)

        self.assertTrue(Photo.objects.filter(file="ghost.jpg").exists())

    def test_counts_every_missing_row(self):
        create_photo(self.album, "one.jpg")
        create_photo(self.album, "two.jpg")

        output = self.run_command(COMMAND, db=True)

        self.assertIn("2 photos in database but not on file", output)

    def test_an_empty_database_reports_ok(self):
        output = self.run_command(COMMAND, db=True)

        self.assertIn("OK", output)

    def test_both_passes_can_run_together(self):
        create_photo(self.album, "ghost.jpg")
        directory = os.path.join(self.photo_root, "2024")
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "stray.jpg"), "wb") as handle:
            handle.write(b"not really an image")

        output = self.run_command(COMMAND, files=True, db=True)

        self.assertIn("Photos not uploaded to database", output)
        self.assertIn("Photos in database but not on file", output)
