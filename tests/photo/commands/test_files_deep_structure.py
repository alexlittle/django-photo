"""Tests for the ``files_deep_structure`` management command.

Reports albums whose name has more path segments than the given --count.
"/2024/" is one segment deep, "/2024/holiday/" is two.
"""

from tests.base import CommandTestCase, create_album, set_site_domain

COMMAND = "files_deep_structure"


class FilesDeepStructureTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        set_site_domain("photos.example.test")

    def test_a_deeper_album_is_reported(self):
        create_album("/2024/holiday/beach/", title="Beach")

        output = self.run_command(COMMAND, count="2")

        self.assertIn("/2024/holiday/beach/", output)
        self.assertIn("1 directories deeper than 2", output)

    def test_an_album_at_the_limit_is_not_reported(self):
        create_album("/2024/holiday/", title="Holiday")

        output = self.run_command(COMMAND, count="2")

        self.assertNotIn("/2024/holiday/", output)
        self.assertIn("OK", output)

    def test_a_shallower_album_is_not_reported(self):
        create_album("/2024/", title="Year")

        output = self.run_command(COMMAND, count="2")

        self.assertIn("OK", output)

    def test_leading_and_trailing_slashes_do_not_count_as_segments(self):
        # filter(None, ...) drops the empty strings either side.
        create_album("/2024/", title="Year")

        output = self.run_command(COMMAND, count="1")

        self.assertIn("OK", output)

    def test_every_deep_album_is_counted(self):
        create_album("/2024/holiday/beach/", title="Beach")
        create_album("/2023/trip/city/", title="City")
        create_album("/2022/", title="Shallow")

        output = self.run_command(COMMAND, count="2")

        self.assertIn("2 directories deeper than 2", output)

    def test_the_header_names_the_threshold(self):
        output = self.run_command(COMMAND, count="3")

        self.assertIn("Finds albums deeper than 3", output)

    def test_no_albums_at_all_reports_ok(self):
        output = self.run_command(COMMAND, count="2")

        self.assertIn("OK", output)

    def test_the_album_title_is_included(self):
        create_album("/2024/holiday/beach/", title="Beach Trip")

        output = self.run_command(COMMAND, count="2")

        self.assertIn("Beach Trip", output)

    def test_an_album_with_no_title_still_reports(self):
        create_album("/2024/holiday/beach/")

        output = self.run_command(COMMAND, count="2")

        self.assertIn("/2024/holiday/beach/", output)

    def test_a_count_of_zero_reports_everything(self):
        create_album("/2024/", title="Year")

        output = self.run_command(COMMAND, count="0")

        self.assertIn("1 directories deeper than 0", output)

    def test_the_album_link_is_well_formed(self):
        album = create_album("/2024/holiday/beach/", title="Beach")

        output = self.run_command(COMMAND, count="2")

        self.assertIn(f"https://photos.example.test/album/{album.id}/", output)

    def test_a_missing_count_argument_is_reported_cleanly(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND)

    def test_a_non_numeric_count_is_reported_cleanly(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND, count="deep")
