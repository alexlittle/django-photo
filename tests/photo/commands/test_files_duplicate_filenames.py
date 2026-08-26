"""Tests for the ``files_duplicate_filenames`` management command.

Groups photos by filename and reports any name used more than once.

Important context: ``Photo.file`` is declared ``unique=True``, and that
uniqueness is global rather than per-album. While that constraint is in place
the count can never exceed one, so the reporting branch of this command is
unreachable and it will always print OK. The tests below cover the reachable
behaviour and pin the constraint that makes the rest dead.
"""

from django.db import IntegrityError, transaction
from django.test import override_settings

from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "files_duplicate_filenames"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class FilesDuplicateFilenamesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_no_photos_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Photos with same filename", output)
        self.assertIn("OK", output)

    def test_distinct_filenames_report_ok(self):
        create_photo(self.album, "a.jpg")
        create_photo(self.album, "b.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)
        self.assertNotIn("duplicates of", output)

    def test_the_same_filename_cannot_be_stored_twice(self):
        # This is why the command's reporting branch is dead code.
        create_photo(self.album, "a.jpg")

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_photo(self.album, "a.jpg")

    def test_the_same_filename_cannot_be_reused_across_albums(self):
        # The unique constraint is global, not scoped to the album -- two
        # albums cannot both hold a DSC_0001.jpg.
        other = create_album("/2023/")
        create_photo(self.album, "DSC_0001.jpg")

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_photo(other, "DSC_0001.jpg")

    def test_filenames_differing_only_by_case_are_treated_separately(self):
        # Whether these collide depends on the database collation: MySQL's
        # default is case-insensitive and would reject the second row, SQLite
        # is case-sensitive and accepts it. Worth knowing if this suite is ever
        # run against both.
        create_photo(self.album, "a.jpg")
        try:
            with transaction.atomic():
                create_photo(self.album, "A.jpg")
        except IntegrityError:
            self.skipTest("database collation treats filenames case-insensitively")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_the_summary_sections_are_always_printed(self):
        create_photo(self.album, "a.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("Photos with same filename", output)
        self.assertIn("---------------------------------------", output)
