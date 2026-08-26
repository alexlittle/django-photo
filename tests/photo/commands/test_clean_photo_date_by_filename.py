"""Tests for the ``clean_photo_date_by_filename`` management command.

The command takes a date and an album, finds the photos in that album stored
against that date, and re-dates each one from digits embedded in its filename:
characters 4-7 are the year, 8-9 the month, 10-11 the day. So ``IMG_20240115``
becomes 2024-01-15.
"""

from datetime import date
from unittest import expectedFailure

from django.core.management.base import CommandError

from photo.models import Album, Photo
from tests.base import CommandTestCase, create_album, create_photo, local, make_datetime

COMMAND = "clean_photo_date_by_filename"


class CleanPhotoDateByFilenameTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.wrong_date = make_datetime(2024, 1, 1)

    def redate(self, photo):
        photo.refresh_from_db()
        return local(photo.date).date()

    def test_photo_is_redated_from_its_filename(self):
        photo = create_photo(self.album, "IMG_20240115_120000.jpg", self.wrong_date)

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(self.redate(photo), date(2024, 1, 15))

    def test_every_matching_photo_is_redated(self):
        first = create_photo(self.album, "IMG_20240115_120000.jpg", self.wrong_date)
        second = create_photo(self.album, "IMG_20240709_090000.jpg", self.wrong_date)

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(self.redate(first), date(2024, 1, 15))
        self.assertEqual(self.redate(second), date(2024, 7, 9))

    def test_photos_on_a_different_date_are_left_alone(self):
        untouched = create_photo(self.album, "IMG_20240115_120000.jpg", make_datetime(2023, 6, 6))

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(self.redate(untouched), date(2023, 6, 6))

    def test_photos_in_another_album_are_left_alone(self):
        other_album = create_album("/2023/")
        untouched = create_photo(other_album, "IMG_20240115_120000.jpg", self.wrong_date)

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(self.redate(untouched), date(2024, 1, 1))

    def test_the_new_date_is_reported(self):
        create_photo(self.album, "IMG_20240115_120000.jpg", self.wrong_date)

        output = self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertIn("2024-01-15", output)

    def test_nothing_to_do_is_not_an_error(self):
        output = self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(output.strip(), "")

    def test_time_of_day_is_discarded(self):
        # The command assigns a plain date, so the stored time resets to
        # midnight rather than being preserved.
        photo = create_photo(
            self.album, "IMG_20240115_120000.jpg", make_datetime(2024, 1, 1, 17, 20)
        )

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        photo.refresh_from_db()
        stored = local(photo.date)
        self.assertEqual((stored.hour, stored.minute), (0, 0))

    def test_assigning_a_naive_date_warns(self):
        # Documents current behaviour: a datetime.date is assigned straight to a
        # DateTimeField, so Django emits a naive-datetime RuntimeWarning. Any
        # CI running with -W error will fail here. Building an aware datetime
        # in the command would remove it.
        create_photo(self.album, "IMG_20240115_120000.jpg", self.wrong_date)

        with self.assertWarns(RuntimeWarning):
            self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

    def test_unknown_album_raises(self):
        with self.assertRaises(Album.DoesNotExist):
            self.run_command(COMMAND, "2024-01-01", album="9999")

    @expectedFailure
    def test_missing_album_argument_is_reported_cleanly(self):
        # --album is optional, so omitting it reaches Album.objects.get(pk=None)
        # and blows up with a bare DoesNotExist rather than a usable message.
        # Marking it required=True, or raising CommandError, would fix this.
        with self.assertRaises(CommandError):
            self.run_command(COMMAND, "2024-01-01")

    @expectedFailure
    def test_a_malformed_date_argument_is_reported_cleanly(self):
        # "2024" splits into one part, so date[1] raises IndexError before any
        # validation happens.
        with self.assertRaises(CommandError):
            self.run_command(COMMAND, "2024", album=str(self.album.id))

    @expectedFailure
    def test_a_filename_without_a_date_is_skipped(self):
        # int("otos") raises ValueError and takes the whole run down, so one bad
        # filename in an album stops every later photo being processed.
        create_photo(self.album, "holiday-photos.jpg", self.wrong_date)
        later = create_photo(self.album, "IMG_20240115_120000.jpg", self.wrong_date)

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(self.redate(later), date(2024, 1, 15))

    @expectedFailure
    def test_an_impossible_date_in_the_filename_is_skipped(self):
        # Month 99 raises ValueError out of datetime.date().
        create_photo(self.album, "IMG_20249915_120000.jpg", self.wrong_date)

        self.run_command(COMMAND, "2024-01-01", album=str(self.album.id))

        self.assertEqual(Photo.objects.filter(album=self.album).count(), 1)
