"""Tests for the ``integrity_small_albums`` management command.

Reports albums holding fewer than --count photos.
"""

from unittest import expectedFailure

from django.test import override_settings
from django.urls import reverse

from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "integrity_small_albums"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class IntegritySmallAlbumsTests(CommandTestCase):
    def test_a_small_album_is_reported(self):
        album = create_album("/2024/", title="Holiday")
        create_photo(album, "a.jpg")

        output = self.run_command(COMMAND, count="3")

        self.assertIn("/2024/", output)
        self.assertIn("[1 photos]", output)
        self.assertIn("1 albums with less than 3 photos", output)

    def test_an_album_at_the_threshold_is_not_reported(self):
        album = create_album("/2024/", title="Holiday")
        create_photo(album, "a.jpg")
        create_photo(album, "b.jpg")
        create_photo(album, "c.jpg")

        output = self.run_command(COMMAND, count="3")

        self.assertNotIn("/2024/", output)
        self.assertIn("OK", output)

    def test_an_empty_album_is_reported(self):
        create_album("/2024/", title="Empty")

        output = self.run_command(COMMAND, count="3")

        self.assertIn("[0 photos]", output)

    def test_every_small_album_is_counted(self):
        first = create_album("/2024/", title="One")
        create_album("/2023/", title="Empty")
        big = create_album("/2022/", title="Big")
        create_photo(first, "a.jpg")
        for name in ("b.jpg", "c.jpg", "d.jpg"):
            create_photo(big, name)

        output = self.run_command(COMMAND, count="3")

        self.assertIn("2 albums with less than 3 photos", output)

    def test_the_header_names_the_threshold(self):
        output = self.run_command(COMMAND, count="7")

        self.assertIn("Albums with less than 7 photos", output)

    def test_no_albums_at_all_reports_ok(self):
        output = self.run_command(COMMAND, count="3")

        self.assertIn("OK", output)

    def test_a_count_of_zero_reports_nothing(self):
        create_album("/2024/", title="Empty")

        output = self.run_command(COMMAND, count="0")

        self.assertIn("OK", output)

    def test_the_album_title_is_included(self):
        create_album("/2024/", title="Beach Trip")

        output = self.run_command(COMMAND, count="3")

        self.assertIn("Beach Trip", output)

    def test_photos_in_other_albums_do_not_count(self):
        small = create_album("/2024/", title="Small")
        big = create_album("/2023/", title="Big")
        create_photo(small, "a.jpg")
        for name in ("b.jpg", "c.jpg", "d.jpg"):
            create_photo(big, name)

        output = self.run_command(COMMAND, count="2")

        self.assertIn("/2024/", output)
        self.assertNotIn("/2023/", output)

    @expectedFailure
    def test_the_album_link_is_well_formed(self):
        # Built as f"{DOMAIN_NAME}/album/{id}", which has the leading slash that
        # files_deep_structure omits but drops the trailing one that
        # photo:album actually uses. Third hand-rolled variant in this command
        # set; reverse("photo:album") would settle all of them.
        album = create_album("/2024/", title="Holiday")

        output = self.run_command(COMMAND, count="3")

        expected = "https://photos.example.test" + reverse(
            "photo:album", kwargs={"album_id": album.id}
        )
        self.assertIn(expected, output)

    @expectedFailure
    def test_a_missing_count_argument_is_reported_cleanly(self):
        # Same as files_deep_structure: --count is optional, so int(None)
        # raises TypeError before anything useful is printed.
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND)
