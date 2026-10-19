"""Tests for the ``generate_thumbnails`` management command."""

from unittest.mock import patch

from photo.management.commands import generate_thumbnails
from photo.models import Photo
from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "generate_thumbnails"


class GenerateThumbnailsTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.photo = create_photo(self.album, "a.jpg")
        patcher = patch.object(Photo, "get_thumbnail")
        self.get_thumbnail = patcher.start()
        self.addCleanup(patcher.stop)

    def sizes_requested(self):
        return [call.args[0] for call in self.get_thumbnail.call_args_list]

    def test_generates_default_sizes(self):
        output = self.run_command(COMMAND)

        self.assertEqual(self.sizes_requested(), generate_thumbnails.DEFAULT_SIZES)
        self.assertIn("Generating thumbnails for 1 photo(s)", output)
        self.assertIn("Done. Generated 2 thumbnail(s), 0 failed.", output)

    def test_custom_sizes(self):
        output = self.run_command(COMMAND, sizes="100, 200,400")

        self.assertEqual(self.sizes_requested(), [100, 200, 400])
        self.assertIn("Generated 3 thumbnail(s)", output)

    def test_invalid_sizes_are_ignored_with_warning(self):
        output = self.run_command(COMMAND, sizes="abc,150,")

        self.assertEqual(self.sizes_requested(), [150])
        self.assertIn("Ignoring invalid thumbnail size: abc", output)

    def test_no_valid_sizes_errors(self):
        output = self.run_command(COMMAND, sizes="abc,")

        self.assertIn("No valid thumbnail sizes given.", output)
        self.get_thumbnail.assert_not_called()

    def test_unknown_album_errors(self):
        output = self.run_command(COMMAND, album="/missing/")

        self.assertIn("Album not found: /missing/", output)
        self.get_thumbnail.assert_not_called()

    def test_album_limits_photos(self):
        other = create_album("/2023/")
        create_photo(other, "b.jpg")

        output = self.run_command(COMMAND, album="/2024/", sizes="100")

        self.assertEqual(self.get_thumbnail.call_count, 1)
        self.assertIn("Generating thumbnails for 1 photo(s)", output)

    def test_failures_are_reported_and_counted(self):
        self.get_thumbnail.side_effect = [OSError("boom"), "url"]

        output = self.run_command(COMMAND)

        self.assertIn(f"Failed thumbnail size 250 for photo {self.photo.id}", output)
        self.assertIn("boom", output)
        self.assertIn("Done. Generated 1 thumbnail(s), 1 failed.", output)

    def test_progress_reported_at_interval(self):
        create_photo(self.album, "b.jpg")
        create_photo(self.album, "c.jpg")

        with patch.object(generate_thumbnails, "PROGRESS_EVERY", 2):
            output = self.run_command(COMMAND, sizes="100")

        self.assertIn("processed 2/3 photos", output)
        self.assertIn("processed 3/3 photos", output)
        self.assertNotIn("processed 1/3 photos", output)
