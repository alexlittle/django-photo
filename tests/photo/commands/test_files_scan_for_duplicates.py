"""Tests for the ``files_scan_for_duplicates`` management command.

Two phases. First it backfills the ``file_hash`` column for any photo missing one.
Then it groups photos by file_hash and, for each group of more than one, prints the members
and prompts for one to delete.

Because ``Photo.file`` is unique, duplicates here mean identical *content* under
different filenames -- unlike files_duplicate_filenames, this one can genuinely
fire.
"""

import os
import re
from unittest import expectedFailure
from unittest.mock import patch

from photo.models import Photo
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "files_scan_for_duplicates"


class FilesScanForDuplicatesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.other = create_album("/2023/")

    def run_with_answers(self, *answers):
        with patch("builtins.input", side_effect=list(answers)) as prompt:
            output = self.run_command(COMMAND)
        return output, prompt

    def make_pair(self):
        """Two photos in different albums with byte-identical content."""
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.other, "b.jpg")
        self.write_image(first)
        self.write_image(second)
        return first, second

    def test_a_hash_is_stored_for_a_photo_that_has_none(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)

        self.run_with_answers()

        photo.refresh_from_db()
        self.assertIsNotNone(photo.file_hash)
        self.assertEqual(len(photo.file_hash), 128, "SHA-512 hex digest")

    def test_hashing_is_reported(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)

        output, _prompt = self.run_with_answers()

        self.assertIn("created md5 for", output)

    def test_a_photo_with_no_file_on_disk_is_left_unhashed(self):
        photo = create_photo(self.album, "ghost.jpg")

        self.run_with_answers()

        photo.refresh_from_db()
        self.assertIsNone(photo.file_hash)

    def test_a_photo_that_already_has_a_hash_is_not_rehashed(self):
        photo = create_photo(self.album, "a.jpg", file_hash="preexisting")
        self.write_image(photo)

        output, _prompt = self.run_with_answers()

        photo.refresh_from_db()
        self.assertEqual(photo.file_hash, "preexisting")
        self.assertNotIn("created hash for", output)

    def test_identical_content_under_different_names_is_flagged(self):
        self.make_pair()

        output, prompt = self.run_with_answers("0")

        self.assertEqual(prompt.call_count, 1)
        self.assertIn("Duplicate:", output)

    def test_different_content_is_not_flagged(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.other, "b.jpg")
        self.write_image(first, size=(40, 40))
        self.write_image(second, size=(80, 80))

        _output, prompt = self.run_with_answers()

        prompt.assert_not_called()

    def test_selecting_an_option_deletes_that_photo(self):
        self.make_pair()

        output, _prompt = self.run_with_answers("1")

        first_listed = int(re.search(r"\[1\] Duplicate: \S+/(\d+)", output).group(1))
        self.assertFalse(Photo.objects.filter(pk=first_listed).exists())
        self.assertEqual(Photo.objects.count(), 1)
        self.assertIn("photo deleted", output)

    def test_deleting_a_duplicate_also_removes_the_file(self):
        # Photo has a post_delete receiver that unlinks the underlying file, so
        # this is a real deletion from disk, not just a database row.
        first, _second = self.make_pair()
        path = os.path.join(self.photo_root, "2024", "a.jpg")

        output, _prompt = self.run_with_answers("1")

        first_listed = int(re.search(r"\[1\] Duplicate: \S+/(\d+)", output).group(1))
        if first_listed == first.pk:
            self.assertFalse(os.path.exists(path))
        else:
            self.assertTrue(os.path.exists(path))

    def test_an_out_of_range_selection_deletes_nothing(self):
        # "0" happens to work as a skip because no option matches it, but that
        # is incidental rather than designed.
        self.make_pair()

        self.run_with_answers("0")

        self.assertEqual(Photo.objects.count(), 2)

    def test_each_duplicate_group_is_prompted_separately(self):
        self.make_pair()
        third = create_photo(self.album, "c.jpg")
        fourth = create_photo(self.other, "d.jpg")
        self.write_image(third, size=(80, 80))
        self.write_image(fourth, size=(80, 80))

        _output, prompt = self.run_with_answers("0", "0")

        self.assertEqual(prompt.call_count, 2)

    def test_photos_are_grouped_by_content_not_album(self):
        self.make_pair()

        output, _prompt = self.run_with_answers("0")

        self.assertIn("/2024/", output)
        self.assertIn("/2023/", output)

    def test_nothing_at_all_is_a_quiet_no_op(self):
        output, prompt = self.run_with_answers()

        prompt.assert_not_called()
        self.assertEqual(output.strip(), "")

    @expectedFailure
    def test_a_non_numeric_selection_is_handled(self):
        # int(select_input) is unguarded, so pressing enter or typing "skip"
        # raises ValueError and abandons the remaining duplicate groups. An
        # explicit skip option would be worth adding while this is interactive.
        self.make_pair()

        self.run_with_answers("")

        self.assertEqual(Photo.objects.count(), 2)

    @expectedFailure
    def test_the_edit_link_uses_the_configured_domain(self):
        # The URL is hardcoded to http://localhost.photo/photo/edit/<id>, which
        # is a dev host baked into a command that also deletes files. Every
        # other command in this set uses settings.DOMAIN_NAME.
        self.make_pair()

        output, _prompt = self.run_with_answers("0")

        self.assertNotIn("localhost.photo", output)
