"""Tests for the ``integrity_remove_empty_albums`` management command.

Deletes every album with no photos. Destructive, and unlike the --autodelete
flag on files_scan_photos there is no opt-in: running it deletes immediately.
"""

from photo.models import Album, Photo
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "integrity_remove_empty_albums"


class IntegrityRemoveEmptyAlbumsTests(CommandTestCase):
    def test_an_empty_album_is_deleted(self):
        create_album("/2024/")

        self.run_command(COMMAND)

        self.assertFalse(Album.objects.filter(name="/2024/").exists())

    def test_an_album_with_photos_survives(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg")

        self.run_command(COMMAND)

        self.assertTrue(Album.objects.filter(name="/2024/").exists())

    def test_only_the_empty_albums_go(self):
        populated = create_album("/2024/")
        create_photo(populated, "a.jpg")
        create_album("/2023/")
        create_album("/2022/")

        self.run_command(COMMAND)

        self.assertEqual(list(Album.objects.values_list("name", flat=True)), ["/2024/"])

    def test_deletions_are_reported(self):
        create_album("/2024/")

        output = self.run_command(COMMAND)

        self.assertIn("Removing: /2024/", output)
        self.assertIn("1 albums with no photos removed", output)

    def test_the_count_covers_every_album_removed(self):
        create_album("/2024/")
        create_album("/2023/")

        output = self.run_command(COMMAND)

        self.assertIn("2 albums with no photos removed", output)

    def test_nothing_to_do_reports_ok(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("Albums with no photos", output)
        self.assertIn("OK", output)

    def test_an_empty_database_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_photos_in_surviving_albums_are_untouched(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg")
        create_album("/2023/")

        self.run_command(COMMAND)

        self.assertEqual(Photo.objects.count(), 1)

    def test_an_album_becomes_removable_once_its_last_photo_goes(self):
        # Pairs with `files_scan_photos --db --autodelete`: that can empty an
        # album, and this then removes the album itself. Worth knowing the two
        # compose, since neither asks for confirmation.
        album = create_album("/2024/")
        photo = create_photo(album, "a.jpg")

        self.run_command(COMMAND)
        self.assertTrue(Album.objects.filter(pk=album.pk).exists())

        Photo.objects.filter(pk=photo.pk).delete()
        self.run_command(COMMAND)

        self.assertFalse(Album.objects.filter(pk=album.pk).exists())

    def test_the_command_deletes_without_asking(self):
        # No --dry-run and no confirmation prompt: pinning this so that adding
        # one later is a deliberate, visible change.
        create_album("/2024/")

        self.run_command(COMMAND)

        self.assertEqual(Album.objects.count(), 0)
