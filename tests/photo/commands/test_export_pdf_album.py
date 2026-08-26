"""Tests for the ``export_pdf_album`` management command.

A thin wrapper that hands its two options to ``photo.export.create_album.make``,
so these tests only pin the argument plumbing. The PDF generation itself belongs
in tests for ``photo.export``.
"""

from unittest.mock import patch

from tests.base import CommandTestCase, create_album, create_tag

COMMAND = "export_pdf_album"
TARGET = "photo.management.commands.export_pdf_album.create_album.make"


class ExportPdfAlbumTests(CommandTestCase):
    def test_album_is_passed_through(self):
        album = create_album("/2024/")

        with patch(TARGET) as make:
            self.run_command(COMMAND, album=str(album.id))

        make.assert_called_once_with(str(album.id), None)

    def test_tag_is_passed_through(self):
        create_tag("Beach")

        with patch(TARGET) as make:
            self.run_command(COMMAND, tag="beach")

        make.assert_called_once_with(None, "beach")

    def test_both_can_be_given_together(self):
        album = create_album("/2024/")

        with patch(TARGET) as make:
            self.run_command(COMMAND, album=str(album.id), tag="beach")

        make.assert_called_once_with(str(album.id), "beach")

    def test_neither_argument_still_calls_through(self):
        # Both options are optional and unvalidated, so a bare run reaches
        # create_album.make(None, None) rather than being rejected.
        with patch(TARGET) as make:
            self.run_command(COMMAND)

        make.assert_called_once_with(None, None)

    def test_an_album_id_that_does_not_exist_is_not_checked(self):
        # The command does no lookup of its own -- validation is entirely
        # create_album.make's problem.
        with patch(TARGET) as make:
            self.run_command(COMMAND, album="9999")

        make.assert_called_once_with("9999", None)

    def test_errors_from_the_exporter_are_not_swallowed(self):
        with patch(TARGET, side_effect=RuntimeError("boom")), self.assertRaises(RuntimeError):
            self.run_command(COMMAND, album="1")
