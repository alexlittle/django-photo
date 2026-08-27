"""Tests for the ``integrity_album_covers`` management command.

Two reports over every album: those with no cover photo, then those with more
than one. The logic lives in ``Album.has_cover`` / ``Album.has_multiple_covers``,
which this command drives one album at a time.
"""

from django.urls import reverse

from tests.base import CommandTestCase, create_album, create_photo, set_site_domain

COMMAND = "integrity_album_covers"


class IntegrityAlbumCoversTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        set_site_domain("photos.example.test")

    def test_an_album_with_no_cover_is_reported(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/", output)
        self.assertIn("1 albums without covers", output)

    def test_an_album_with_one_cover_is_not_reported(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg", album_cover=True)

        output = self.run_command(COMMAND)

        self.assertNotIn("albums without covers", output)
        self.assertNotIn("albums with multiple covers", output)

    def test_an_empty_album_counts_as_having_no_cover(self):
        create_album("/2024/")

        output = self.run_command(COMMAND)

        self.assertIn("1 albums without covers", output)

    def test_an_album_with_two_covers_is_reported_as_multiple(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg", album_cover=True)
        create_photo(album, "b.jpg", album_cover=True)

        output = self.run_command(COMMAND)

        self.assertIn("1 albums with multiple covers", output)

    def test_an_album_with_two_covers_is_not_also_reported_as_having_none(self):
        # has_cover() swallows MultipleObjectsReturned and returns True, so an
        # over-covered album appears in the second report only.
        album = create_album("/2024/")
        create_photo(album, "a.jpg", album_cover=True)
        create_photo(album, "b.jpg", album_cover=True)

        output = self.run_command(COMMAND)

        self.assertNotIn("albums without covers", output)

    def test_covers_are_counted_per_album(self):
        first = create_album("/2024/")
        second = create_album("/2023/")
        create_photo(first, "a.jpg", album_cover=True)
        create_photo(second, "b.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("/2023/", output)
        self.assertIn("1 albums without covers", output)

    def test_every_uncovered_album_is_counted(self):
        create_album("/2024/")
        create_album("/2023/")
        create_album("/2022/")

        output = self.run_command(COMMAND)

        self.assertIn("3 albums without covers", output)

    def test_the_link_uses_the_album_url(self):
        album = create_album("/2024/")

        output = self.run_command(COMMAND)

        expected = "https://photos.example.test" + reverse(
            "photo:album", kwargs={"album_id": album.id}
        )
        self.assertIn(expected, output)

    def test_both_sections_are_always_printed(self):
        output = self.run_command(COMMAND)

        self.assertIn("No cover:", output)
        self.assertIn("Multiple covers:", output)

    def test_no_albums_at_all_reports_ok_twice(self):
        output = self.run_command(COMMAND)

        self.assertEqual(output.count("OK"), 2)

    def test_a_cover_in_another_album_does_not_satisfy_this_one(self):
        covered = create_album("/2024/")
        uncovered = create_album("/2023/")
        create_photo(covered, "a.jpg", album_cover=True)
        create_photo(uncovered, "b.jpg")

        output = self.run_command(COMMAND)

        self.assertIn(uncovered.name, output)
        self.assertIn("1 albums without covers", output)
