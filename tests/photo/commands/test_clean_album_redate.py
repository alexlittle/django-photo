"""Tests for the ``clean_album_redate`` management command.

Sets every photo in one album to a single date given on the command line.
Unlike ``clean_photo_date_by_filename`` it does not filter by existing date --
the whole album is rewritten.
"""

from datetime import date
from unittest import expectedFailure

from django.core.management.base import CommandError

from photo.models import Album
from tests.base import CommandTestCase, create_album, create_photo, local, make_datetime

COMMAND = "clean_album_redate"


class CleanAlbumRedateTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def stored_date(self, photo):
        photo.refresh_from_db()
        return local(photo.date).date()

    def test_every_photo_in_the_album_is_redated(self):
        first = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        second = create_photo(self.album, "b.jpg", make_datetime(2021, 6, 6))

        self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

        self.assertEqual(self.stored_date(first), date(2024, 3, 9))
        self.assertEqual(self.stored_date(second), date(2024, 3, 9))

    def test_photos_in_other_albums_are_untouched(self):
        other = create_album("/2023/")
        untouched = create_photo(other, "b.jpg", make_datetime(2021, 6, 6))

        self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

        self.assertEqual(self.stored_date(untouched), date(2021, 6, 6))

    def test_an_empty_album_is_not_an_error(self):
        output = self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

        self.assertEqual(output.strip(), "")

    def test_the_existing_date_is_irrelevant(self):
        # No date filter here, so a photo already on the target date is still
        # rewritten (and loses its time of day).
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9, 17, 20))

        self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

        photo.refresh_from_db()
        stored = local(photo.date)
        self.assertEqual((stored.hour, stored.minute), (0, 0))

    def test_time_of_day_is_discarded(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1, 14, 30))

        self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

        photo.refresh_from_db()
        stored = local(photo.date)
        self.assertEqual((stored.hour, stored.minute), (0, 0))

    def test_assigning_a_naive_date_warns(self):
        # As with the other redate commands: a datetime.date goes straight into
        # a DateTimeField, so Django emits a naive-datetime RuntimeWarning.
        create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))

        with self.assertWarns(RuntimeWarning):
            self.run_command(COMMAND, "2024-03-09", album=str(self.album.id))

    def test_unknown_album_raises(self):
        with self.assertRaises(Album.DoesNotExist):
            self.run_command(COMMAND, "2024-03-09", album="9999")

    def test_the_date_is_parsed_before_the_album_is_looked_up(self):
        # Ordering matters for what the user sees first: a bad date fails even
        # when the album id is also wrong.
        with self.assertRaises(ValueError):
            self.run_command(COMMAND, "2024-99-09", album="9999")

    def test_missing_album_argument_is_reported_cleanly(self):
        with self.assertRaises(CommandError):
            self.run_command(COMMAND, "2024-03-09")

    @expectedFailure
    def test_a_malformed_date_argument_is_reported_cleanly(self):
        # "2024" splits into one part, so date[1] raises IndexError.
        with self.assertRaises(CommandError):
            self.run_command(COMMAND, "2024", album=str(self.album.id))

    @expectedFailure
    def test_a_non_numeric_date_argument_is_reported_cleanly(self):
        with self.assertRaises(CommandError):
            self.run_command(COMMAND, "last-tuesday-ish", album=str(self.album.id))
