"""Tests for the ``clean_redate_photos`` management command.

Reads EXIF from each photo file in an album and rewrites the stored date from
whichever timestamp tag it finds first: DateTimeOriginal, then DateTimeDigitized,
then DateTime. Timestamps are treated as Europe/London.

These use real JPEGs with real EXIF rather than mocking ``get_exif``, so the
parsing in ``photo.lib`` is exercised too.
"""

from datetime import UTC, date
from unittest import expectedFailure
from unittest.mock import patch

from tests.base import CommandTestCase, create_album, create_photo, local, make_datetime

COMMAND = "clean_redate_photos"

DATE_TIME_ORIGINAL = 36867
DATE_TIME_DIGITIZED = 36868
DATE_TIME = 306


class CleanRedatePhotosTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def stored(self, photo):
        photo.refresh_from_db()
        return local(photo.date)

    def test_date_is_taken_from_date_time_original(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(photo, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        stored = self.stored(photo)
        self.assertEqual(stored.date(), date(2024, 3, 9))
        self.assertEqual((stored.hour, stored.minute), (14, 25))

    def test_falls_back_to_date_time_digitized(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(photo, **{str(DATE_TIME_DIGITIZED): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(photo).date(), date(2024, 3, 9))

    def test_falls_back_to_date_time(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(photo, **{str(DATE_TIME): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(photo).date(), date(2024, 3, 9))

    def test_date_time_original_wins_over_the_others(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(
            photo,
            **{
                str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00",
                str(DATE_TIME_DIGITIZED): "2019:01:01 00:00:00",
                str(DATE_TIME): "2018:01:01 00:00:00",
            },
        )

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(photo).date(), date(2024, 3, 9))

    def test_a_photo_with_no_exif_at_all_is_skipped(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image(photo)

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(photo).date(), date(2020, 1, 1))

    def test_updated_photos_are_reported(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(photo, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertIn("Updating dates for... /2024/", output)
        self.assertIn("updated: a.jpg", output)

    def test_every_photo_in_the_album_is_processed(self):
        first = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        second = create_photo(self.album, "b.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(first, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})
        self.write_image_with_exif(second, **{str(DATE_TIME_ORIGINAL): "2023:07:04 09:00:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(first).date(), date(2024, 3, 9))
        self.assertEqual(self.stored(second).date(), date(2023, 7, 4))

    def test_photos_in_other_albums_are_untouched(self):
        other = create_album("/2023/")
        untouched = create_photo(other, "b.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(untouched, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(untouched).date(), date(2020, 1, 1))

    def test_unknown_album_is_handled(self):
        output = self.run_command(COMMAND, album="9999")

        self.assertIn("No Album Specified", output)

    def test_missing_album_argument_is_handled(self):
        # get(id=None) raises DoesNotExist, which this command does catch --
        # unlike its siblings.
        output = self.run_command(COMMAND)

        self.assertIn("No Album Specified", output)

    def test_an_unparseable_timestamp_is_reported_not_fatal(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(photo, **{str(DATE_TIME_ORIGINAL): "not a timestamp"})

        output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertIn("AttributeError a.jpg", output)
        self.assertEqual(self.stored(photo).date(), date(2020, 1, 1))

    def test_timestamps_are_interpreted_as_london(self):
        # The zone is hardcoded to Europe/London, so a July timestamp is read
        # as BST and stored an hour behind in UTC. Asserting in UTC keeps this
        # independent of the project's TIME_ZONE setting.
        summer = create_photo(self.album, "summer.jpg", make_datetime(2020, 1, 1))
        winter = create_photo(self.album, "winter.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(summer, **{str(DATE_TIME_ORIGINAL): "2024:07:04 12:00:00"})
        self.write_image_with_exif(winter, **{str(DATE_TIME_ORIGINAL): "2024:01:04 12:00:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        summer.refresh_from_db()
        winter.refresh_from_db()
        self.assertEqual(summer.date.astimezone(UTC).hour, 11)
        self.assertEqual(winter.date.astimezone(UTC).hour, 12)

    @expectedFailure
    def test_exif_without_any_timestamp_tag_does_not_crash(self):
        # If none of the three tags is present, exif_date is never assigned and
        # the reference raises UnboundLocalError. That inherits from NameError,
        # so none of the KeyError/AttributeError/ValueError handlers catch it
        # and the whole run dies on one bad file. (The `except KeyError` branch
        # looks like it was meant for this, but `in` checks never raise.)
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        # Orientation only -- EXIF present, but no timestamp.
        self.write_image_with_exif(photo, **{"274": 1})
        later = create_photo(self.album, "b.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(later, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(later).date(), date(2024, 3, 9))

    @expectedFailure
    def test_a_missing_file_is_skipped_rather_than_fatal(self):
        # get_exif calls Image.open with no guard, so a database row whose file
        # has gone raises FileNotFoundError and stops the run. Worth pairing
        # with files_scan_photos --db before running this.
        create_photo(self.album, "ghost.jpg", make_datetime(2020, 1, 1))
        later = create_photo(self.album, "b.jpg", make_datetime(2020, 1, 1))
        self.write_image_with_exif(later, **{str(DATE_TIME_ORIGINAL): "2024:03:09 14:25:00"})

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.stored(later).date(), date(2024, 3, 9))

    def test_get_exif_reporting_no_data_skips_the_photo(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2020, 1, 1))
        self.write_image(photo)

        target = "photo.management.commands.clean_redate_photos.get_exif"
        with patch(target, return_value=(None, False)) as get_exif:
            self.run_command(COMMAND, album=str(self.album.id))

        get_exif.assert_called_once()
        self.assertEqual(self.stored(photo).date(), date(2020, 1, 1))
