"""Tests for the ``files_scan_albums`` management command.

Two passes, both always run: directories under PHOTO_ROOT with no Album row,
then Album rows with no directory on disk.
"""

import os
from unittest import expectedFailure

from django.test import override_settings

from tests.base import CommandTestCase, create_album

COMMAND = "files_scan_albums"


@override_settings(IGNORE_FOLDERS=[])
class FilesScanAlbumsTests(CommandTestCase):
    def make_dir(self, *parts):
        path = os.path.join(self.photo_root, *parts)
        os.makedirs(path, exist_ok=True)
        return path

    def test_a_directory_with_no_album_row_is_reported(self):
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/ not found", output)
        self.assertIn("1 directories not in database", output)

    def test_a_directory_with_an_album_row_is_not_reported(self):
        create_album("/2024/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertNotIn("/2024/ not found", output)
        self.assertIn("Directories not in database", output)

    def test_nested_directories_are_walked(self):
        self.make_dir("2024", "holiday")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/ not found", output)
        self.assertIn("/2024/holiday/ not found", output)
        self.assertIn("2 directories not in database", output)

    def test_ignored_folders_are_skipped(self):
        self.make_dir("2024")
        self.make_dir("export")

        with override_settings(IGNORE_FOLDERS=[r"/export.*"]):
            output = self.run_command(COMMAND)

        self.assertNotIn("/export/ not found", output)
        self.assertIn("/2024/ not found", output)

    def test_all_directories_present_reports_ok(self):
        create_album("/2024/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_an_album_row_with_no_directory_is_counted(self):
        create_album("/2024/")
        self.make_dir("2023")
        create_album("/2023/")

        output = self.run_command(COMMAND)

        self.assertIn("Albums in database but not on disk", output)
        self.assertIn("1 albums in database but not on disk", output)

    def test_an_album_row_with_a_directory_is_not_counted(self):
        create_album("/2024/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertNotIn("albums in database but not on disk", output)

    def test_both_sections_are_always_printed(self):
        create_album("/2024/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertIn("Directories not in database", output)
        self.assertIn("Albums in database but not on disk", output)

    def test_a_directory_tree_and_database_that_agree_report_ok_twice(self):
        create_album("/2024/")
        create_album("/2023/")
        self.make_dir("2024")
        self.make_dir("2023")

        output = self.run_command(COMMAND)

        self.assertEqual(output.count("OK"), 2)

    @expectedFailure
    def test_a_missing_album_is_named_correctly(self):
        # The second loop prints `album_path`, which is the leftover loop
        # variable from the *first* loop, not the album it is currently
        # checking. So every missing album is reported under whatever directory
        # the first pass happened to look at last -- and if the first pass never
        # ran (an empty PHOTO_ROOT), the name is unbound and the command dies
        # with UnboundLocalError. Should be `album.name`.
        create_album("/2023/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertIn("/2023/ not found", output)

    @expectedFailure
    def test_an_empty_photo_root_does_not_crash(self):
        # Same root cause: nothing binds album_path, so the second loop raises
        # UnboundLocalError as soon as it finds an album with no directory.
        create_album("/2024/")

        output = self.run_command(COMMAND)

        self.assertIn("1 albums in database but not on disk", output)

    @expectedFailure
    def test_duplicate_album_names_do_not_crash_the_scan(self):
        # Album.name has no unique constraint, so two rows can share a name and
        # Album.objects.get() raises MultipleObjectsReturned, which nothing
        # catches. filter().exists() would be the safer lookup here.
        create_album("/2024/")
        create_album("/2024/")
        self.make_dir("2024")

        output = self.run_command(COMMAND)

        self.assertIn("Directories not in database", output)
