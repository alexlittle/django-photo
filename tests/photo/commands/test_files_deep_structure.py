"""Tests for the ``files_deep_structure`` management command.

Reports albums whose name has more path segments than the given --count.
"/2024/" is one segment deep, "/2024/holiday/" is two.
"""

from unittest import expectedFailure

from django.test import override_settings

from tests.base import CommandTestCase, create_album

COMMAND = "files_deep_structure"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class FilesDeepStructureTests(CommandTestCase):
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

    @expectedFailure
    def test_the_album_link_is_well_formed(self):
        # The URL is built as f"{DOMAIN_NAME}album/{id}" with no separating
        # slash, giving "https://photos.example.testalbum/12". Note the sibling
        # command report_missing_country does DOMAIN_NAME + reverse(...), which
        # yields a leading slash -- so the two disagree about whether
        # DOMAIN_NAME carries a trailing slash. Using reverse("photo:album")
        # here would settle it.
        album = create_album("/2024/holiday/beach/", title="Beach")

        output = self.run_command(COMMAND, count="2")

        self.assertIn(f"https://photos.example.test/album/{album.id}", output)

    @expectedFailure
    def test_a_missing_count_argument_is_reported_cleanly(self):
        # --count is optional, so int(None) raises TypeError before anything
        # useful is printed. Either default it or mark it required.
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND)

    @expectedFailure
    def test_a_non_numeric_count_is_reported_cleanly(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_command(COMMAND, count="deep")
