"""Tests for the ``clean_rename_files`` management command.

Thin wrapper: for each photo in an album it calls ``photo.lib.rename_photo_file``,
which appends "-<photo id>" before the extension and renames the file on disk.
The real lib function runs here -- it is plain os.rename, no external tooling.
"""

import os

from photo.models import Album
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "clean_rename_files"


class CleanRenameFilesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_file_is_renamed_on_disk_and_in_the_database(self):
        photo = create_photo(self.album, "a.jpg")
        old_path = self.write_image(photo)

        self.run_command(COMMAND, album=str(self.album.id))

        photo.refresh_from_db()
        self.assertEqual(photo.file, f"a-{photo.id}.jpg")
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(os.path.join(self.photo_root, "2024", photo.file)))

    def test_every_photo_in_the_album_is_renamed(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")
        self.write_image(first)
        self.write_image(second)

        self.run_command(COMMAND, album=str(self.album.id))

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.file, f"a-{first.id}.jpg")
        self.assertEqual(second.file, f"b-{second.id}.jpg")

    def test_photos_in_other_albums_are_untouched(self):
        other = create_album("/2023/")
        untouched = create_photo(other, "b.jpg")
        self.write_image(untouched)

        self.run_command(COMMAND, album=str(self.album.id))

        untouched.refresh_from_db()
        self.assertEqual(untouched.file, "b.jpg")

    def test_a_missing_file_leaves_the_database_row_alone(self):
        photo = create_photo(self.album, "ghost.jpg")

        output = self.run_command(COMMAND, album=str(self.album.id))

        photo.refresh_from_db()
        self.assertEqual(photo.file, "ghost.jpg")
        self.assertIn("File not found: ghost.jpg", output)

    def test_a_missing_file_does_not_stop_later_photos(self):
        create_photo(self.album, "ghost.jpg")
        later = create_photo(self.album, "b.jpg")
        self.write_image(later)

        self.run_command(COMMAND, album=str(self.album.id))

        later.refresh_from_db()
        self.assertEqual(later.file, f"b-{later.id}.jpg")

    def test_an_empty_album_is_not_an_error(self):
        output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(output.strip(), "")

    def test_unknown_album_raises(self):
        with self.assertRaises(Album.DoesNotExist):
            self.run_command(COMMAND, album="9999")

    def test_the_suffix_goes_before_the_first_dot_not_the_extension(self):
        # rename_photo_file uses file.replace(".", "-<id>.", 1), so a filename
        # containing more than one dot gets the id inserted at the first one.
        photo = create_photo(self.album, "my.holiday.jpg")
        self.write_image(photo)

        self.run_command(COMMAND, album=str(self.album.id))

        photo.refresh_from_db()
        self.assertEqual(photo.file, f"my-{photo.id}.holiday.jpg")

    def test_running_twice_appends_the_id_twice(self):
        # Not idempotent -- a second pass turns a-7.jpg into a-7-7.jpg. Worth
        # knowing before scripting this against a whole library.
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)

        self.run_command(COMMAND, album=str(self.album.id))
        photo.refresh_from_db()
        first_pass = photo.file

        self.run_command(COMMAND, album=str(self.album.id))
        photo.refresh_from_db()

        self.assertEqual(first_pass, f"a-{photo.id}.jpg")
        self.assertEqual(photo.file, f"a-{photo.id}-{photo.id}.jpg")

    def test_missing_album_argument_is_reported_cleanly(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND)
