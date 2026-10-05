"""Tests for the ``files_scan_videos`` management command.

The video counterpart of ``files_scan_photos``: --files reports videos on disk
with no database row, --db reports video rows whose file is missing. Photos are
ignored here, and videos are ignored by ``files_scan_photos``.
"""

import os

from django.core.management.base import CommandError
from django.test import override_settings

from photo.models import Photo
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "files_scan_videos"


@override_settings(IGNORE_FOLDERS=[], IGNORE_EXTENSIONS=[".db", ".ini"])
class FilesScanVideosTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def touch(self, filename, album_name="/2024/"):
        directory = os.path.join(self.photo_root, album_name.lstrip("/"))
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, filename)
        with open(path, "wb") as handle:
            handle.write(b"not really a video")
        return path

    def test_without_flags_the_command_errors(self):
        with self.assertRaises(CommandError):
            self.run_command(COMMAND)

    def test_reports_a_video_with_no_database_row(self):
        self.touch("orphan.mp4")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("Videos not uploaded to database", output)
        self.assertIn("/2024/orphan.mp4", output)
        self.assertIn("notfound", output)
        self.assertIn("1 videos not in database", output)

    def test_uppercase_extensions_are_recognised(self):
        self.touch("LOUD.MOV")

        output = self.run_command(COMMAND, files=True)

        self.assertIn("/2024/LOUD.MOV", output)

    def test_a_video_with_a_row_is_not_reported(self):
        create_photo(self.album, "known.mp4")
        self.touch("known.mp4")

        output = self.run_command(COMMAND, files=True)

        self.assertNotIn("notfound", output)
        self.assertIn("OK", output)

    def test_verbose_lists_videos_that_were_found(self):
        create_photo(self.album, "known.mp4")
        self.touch("known.mp4")

        output = self.run_command(COMMAND, files=True, verbose=True)

        self.assertIn("/2024/known.mp4 found", output)

    def test_photos_on_disk_are_ignored(self):
        self.touch("orphan.jpg")

        output = self.run_command(COMMAND, files=True)

        self.assertNotIn("orphan.jpg", output)

    def test_videos_are_found_even_when_ignore_extensions_lists_them(self):
        # Real settings list .mp4/.mov etc. in IGNORE_EXTENSIONS so the photo
        # scanner skips them; that must not hide them from the video scanner.
        self.touch("orphan.mp4")

        with override_settings(IGNORE_EXTENSIONS=[".mp4", ".mov", ".db"]):
            output = self.run_command(COMMAND, files=True)

        self.assertIn("/2024/orphan.mp4", output)

    def test_ignored_extensions_and_folders_are_skipped(self):
        self.touch("Thumbs.db")
        self.touch("hidden.mp4", album_name="/.thumbnails/")

        with override_settings(IGNORE_FOLDERS=[r".*\.thumbnails.*"]):
            output = self.run_command(COMMAND, files=True)

        self.assertNotIn("Thumbs.db", output)
        self.assertNotIn("hidden.mp4", output)

    def test_db_pass_reports_a_video_row_with_no_file(self):
        create_photo(self.album, "ghost.mp4")

        output = self.run_command(COMMAND, db=True)

        self.assertIn("Videos in database but not on file", output)
        self.assertIn("/2024/ghost.mp4 not found", output)
        self.assertIn("1 videos in database but not on file", output)

    def test_db_pass_ignores_photo_rows(self):
        create_photo(self.album, "ghost.jpg")

        output = self.run_command(COMMAND, db=True)

        self.assertNotIn("ghost.jpg", output)
        self.assertIn("OK", output)

    def test_db_pass_finds_existing_video(self):
        create_photo(self.album, "known.mp4")
        self.touch("known.mp4")

        output = self.run_command(COMMAND, db=True, verbose=True)

        self.assertIn("/2024/known.mp4 found", output)
        self.assertNotIn("not found", output)

    def test_autodelete_removes_only_missing_video_rows(self):
        create_photo(self.album, "ghost.mp4")
        create_photo(self.album, "ghost.jpg")
        create_photo(self.album, "known.mp4")
        self.touch("known.mp4")

        output = self.run_command(COMMAND, db=True, autodelete=True)

        self.assertFalse(Photo.objects.filter(file="ghost.mp4").exists())
        self.assertTrue(Photo.objects.filter(file="ghost.jpg").exists())
        self.assertTrue(Photo.objects.filter(file="known.mp4").exists())
        self.assertIn("... DELETED", output)


@override_settings(IGNORE_FOLDERS=[], IGNORE_EXTENSIONS=[".db", ".ini"])
class FilesScanPhotosIgnoreVideosTests(CommandTestCase):
    """files_scan_photos must leave videos to files_scan_videos."""

    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_files_pass_skips_videos(self):
        directory = os.path.join(self.photo_root, "2024")
        os.makedirs(directory)
        with open(os.path.join(directory, "clip.mp4"), "wb") as handle:
            handle.write(b"x")

        output = self.run_command("files_scan_photos", files=True)

        self.assertNotIn("clip.mp4", output)

    def test_db_pass_skips_videos(self):
        create_photo(self.album, "ghost.mp4")

        output = self.run_command("files_scan_photos", db=True)

        self.assertNotIn("ghost.mp4", output)
