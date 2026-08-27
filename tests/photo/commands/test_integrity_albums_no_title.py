"""Tests for the ``integrity_albums_no_title`` management command.

Reports albums with no title set.
"""

from django.urls import reverse

from tests.base import CommandTestCase, create_album, set_site_domain

COMMAND = "integrity_albums_no_title"


class IntegrityAlbumsNoTitleTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        set_site_domain("photos.example.test")

    def test_an_album_with_no_title_is_reported(self):
        create_album("/2024/")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/", output)
        self.assertIn("1 albums without a title", output)

    def test_an_album_with_a_title_is_not_reported(self):
        create_album("/2024/", title="Holiday")

        output = self.run_command(COMMAND)

        self.assertNotIn("/2024/", output)
        self.assertIn("OK", output)

    def test_every_untitled_album_is_counted(self):
        create_album("/2024/")
        create_album("/2023/")
        create_album("/2022/", title="Titled")

        output = self.run_command(COMMAND)

        self.assertIn("2 albums without a title", output)

    def test_no_albums_at_all_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Albums with no title", output)
        self.assertIn("OK", output)

    def test_the_link_uses_the_album_url(self):
        album = create_album("/2024/")

        output = self.run_command(COMMAND)

        expected = "https://photos.example.test" + reverse(
            "photo:album", kwargs={"album_id": album.id}
        )
        self.assertIn(expected, output)

    def test_a_whitespace_title_is_treated_as_set(self):
        # Documents current behaviour rather than endorsing it: a title of " "
        # is not NULL, so it passes.
        create_album("/2024/", title=" ")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_an_empty_string_title_is_reported(self):
        create_album("/2024/", title="")

        output = self.run_command(COMMAND)

        self.assertIn("1 albums without a title", output)
