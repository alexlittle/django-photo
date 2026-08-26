"""Tests for the ``clean_rewrite_exif_data`` management command.

Walks an album and calls ``photo.lib.add_or_update_xmp_metadata`` on each photo.

That function drives libxmp against real files, so it is patched here at the
command module (where the name is bound). Testing the XMP writing itself needs
libxmp plus the native exempi library, which belongs in a separate test_lib
module rather than in the command tests.
"""

from unittest.mock import patch

from tests.base import CommandTestCase, create_album, create_photo

COMMAND = "clean_rewrite_exif_data"
TARGET = "photo.management.commands.clean_rewrite_exif_data.add_or_update_xmp_metadata"


class CleanRewriteExifDataTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/", title="Holiday")

    def test_metadata_is_written_for_every_photo_in_the_album(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")

        with patch(TARGET) as write_xmp:
            self.run_command(COMMAND, album=str(self.album.id))

        written = [call.args[0] for call in write_xmp.call_args_list]
        self.assertCountEqual(written, [first, second])

    def test_photos_in_other_albums_are_skipped(self):
        create_photo(self.album, "a.jpg")
        other = create_album("/2023/")
        elsewhere = create_photo(other, "b.jpg")

        with patch(TARGET) as write_xmp:
            self.run_command(COMMAND, album=str(self.album.id))

        written = [call.args[0] for call in write_xmp.call_args_list]
        self.assertNotIn(elsewhere, written)

    def test_the_album_and_each_photo_are_reported(self):
        create_photo(self.album, "a.jpg")

        with patch(TARGET):
            output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertIn("/2024/", output)
        self.assertIn("a.jpg", output)

    def test_an_empty_album_writes_nothing(self):
        with patch(TARGET) as write_xmp:
            output = self.run_command(COMMAND, album=str(self.album.id))

        write_xmp.assert_not_called()
        self.assertIn("/2024/", output)

    def test_unknown_album_is_handled(self):
        with patch(TARGET) as write_xmp:
            output = self.run_command(COMMAND, album="9999")

        self.assertIn("Album not found", output)
        write_xmp.assert_not_called()

    def test_missing_album_argument_is_handled(self):
        # get(id=None) raises DoesNotExist, which this command catches.
        with patch(TARGET) as write_xmp:
            output = self.run_command(COMMAND)

        self.assertIn("Album not found", output)
        write_xmp.assert_not_called()

    def test_a_failure_on_one_photo_stops_the_run(self):
        # add_or_update_xmp_metadata swallows its own exceptions internally, so
        # in practice this does not fire -- but the command has no guard of its
        # own, so anything that does escape takes the whole album down.
        create_photo(self.album, "a.jpg")
        create_photo(self.album, "b.jpg")

        with (
            patch(TARGET, side_effect=RuntimeError("boom")) as write_xmp,
            self.assertRaises(RuntimeError),
        ):
            self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(write_xmp.call_count, 1)
