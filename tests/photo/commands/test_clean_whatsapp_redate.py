"""Tests for the ``clean_whatsapp_redate`` management command.

Looks at photos in one album whose filename starts "img-" (WhatsApp exports
like IMG-20240115-WA0001.jpg), reads the date out of characters 4-11, and if it
disagrees with the stored date, rewrites it and adds year/month tags.
"""

from datetime import date

from photo.models import Tag
from tests.base import (
    CommandTestCase,
    create_album,
    create_photo,
    create_tag,
    local,
    make_datetime,
    tag_photo,
)

COMMAND = "clean_whatsapp_redate"


class CleanWhatsappRedateTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def stored_date(self, photo):
        photo.refresh_from_db()
        return local(photo.date).date()

    def tags_for(self, photo):
        return sorted(Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True))

    def test_a_mismatched_date_is_corrected_from_the_filename(self):
        photo = create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.stored_date(photo), date(2024, 1, 15))

    def test_year_and_month_tags_are_added(self):
        photo = create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.tags_for(photo), ["2024", "January"])

    def test_a_matching_date_is_left_alone_and_untagged(self):
        photo = create_photo(
            self.album, "IMG-20240115-WA0001.jpg", make_datetime(2024, 1, 15, 17, 20)
        )

        self.run_command(COMMAND, str(self.album.id))

        photo.refresh_from_db()
        stored = local(photo.date)
        self.assertEqual((stored.hour, stored.minute), (17, 20))
        self.assertEqual(self.tags_for(photo), [])

    def test_files_not_starting_img_are_ignored(self):
        untouched = create_photo(self.album, "DSC_20240115.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.stored_date(untouched), date(2020, 1, 1))

    def test_the_filename_prefix_match_is_case_insensitive(self):
        photo = create_photo(self.album, "img-20240115-wa0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.stored_date(photo), date(2024, 1, 15))

    def test_photos_in_other_albums_are_ignored(self):
        other = create_album("/2023/")
        untouched = create_photo(other, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.stored_date(untouched), date(2020, 1, 1))

    def test_every_photo_is_reported(self):
        create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        output = self.run_command(COMMAND, str(self.album.id))

        self.assertIn("IMG-20240115-WA0001.jpg", output)

    def test_an_unknown_album_id_is_a_quiet_no_op(self):
        # Filtering on album__pk rather than Album.objects.get means a wrong id
        # just matches nothing instead of raising.
        output = self.run_command(COMMAND, "9999")

        self.assertEqual(output.strip(), "")

    def test_time_of_day_is_discarded_when_redating(self):
        photo = create_photo(
            self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1, 14, 30)
        )

        self.run_command(COMMAND, str(self.album.id))

        photo.refresh_from_db()
        stored = local(photo.date)
        self.assertEqual((stored.hour, stored.minute), (0, 0))

    def test_existing_date_tags_are_reused(self):
        existing = create_tag("2024")
        create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(Tag.objects.filter(name="2024").count(), 1)
        self.assertEqual(Tag.objects.get(name="2024").id, existing.id)

    def test_created_date_tags_land_in_the_date_category(self):
        from photo.models import TagCategory

        date_category = TagCategory.objects.create(name="Date")
        create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(Tag.objects.get(name="2024").tagcategory, date_category)

    def test_stale_date_tags_are_removed(self):
        stale = create_tag("2020")
        photo = create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))
        tag_photo(photo, stale)

        self.run_command(COMMAND, str(self.album.id))

        self.assertNotIn("2020", self.tags_for(photo))

    def test_an_img_file_without_a_date_is_skipped(self):
        create_photo(self.album, "img-holiday.jpg", make_datetime(2020, 1, 1))
        later = create_photo(self.album, "IMG-20240115-WA0001.jpg", make_datetime(2020, 1, 1))

        self.run_command(COMMAND, str(self.album.id))

        self.assertEqual(self.stored_date(later), date(2024, 1, 15))
