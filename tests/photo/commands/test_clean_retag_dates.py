"""Tests for the ``clean_retag_dates`` management command.

For each photo in an album: drop any tags in the "Date" category, then add a
year tag and a month tag derived from the stored date.
"""

from photo.models import Album, Tag, TagCategory
from tests.base import (
    CommandTestCase,
    create_album,
    create_photo,
    create_tag,
    make_datetime,
    tag_photo,
)

COMMAND = "clean_retag_dates"


class CleanRetagDatesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/", title="Holiday")
        self.date_category = TagCategory.objects.create(name="Date")

    def tags_for(self, photo):
        return sorted(Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True))

    def test_year_and_month_tags_are_added(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(photo), ["2024", "March"])

    def test_every_photo_in_the_album_is_tagged(self):
        first = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))
        second = create_photo(self.album, "b.jpg", make_datetime(2023, 7, 4))

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(first), ["2024", "March"])
        self.assertEqual(self.tags_for(second), ["2023", "July"])

    def test_photos_sharing_a_month_share_the_tag(self):
        first = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))
        second = create_photo(self.album, "b.jpg", make_datetime(2024, 3, 20))

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(Tag.objects.filter(name="March").count(), 1)
        self.assertEqual(self.tags_for(first), self.tags_for(second))

    def test_non_date_tags_survive(self):
        beach = create_tag("Beach")
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))
        tag_photo(photo, beach)

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(photo), ["2024", "Beach", "March"])

    def test_existing_date_category_tags_are_cleared_first(self):
        stale = create_tag("1999", self.date_category)
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))
        tag_photo(photo, stale)

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertNotIn("1999", self.tags_for(photo))

    def test_existing_date_tags_are_reused_when_already_categorised(self):
        existing = create_tag("2024", self.date_category)
        create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(Tag.objects.filter(name="2024").count(), 1)
        self.assertEqual(Tag.objects.get(name="2024").id, existing.id)

    def test_photos_in_other_albums_are_untouched(self):
        other = create_album("/2023/")
        untouched = create_photo(other, "b.jpg", make_datetime(2023, 7, 4))

        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(untouched), [])

    def test_running_twice_does_not_duplicate(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))

        self.run_command(COMMAND, album=str(self.album.id))
        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(photo), ["2024", "March"])

    def test_progress_is_reported(self):
        create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))

        output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertIn("Retagging date tags for Holiday", output)
        self.assertIn("Added date tags: 2024 March", output)

    def test_an_empty_album_prints_only_the_header(self):
        output = self.run_command(COMMAND, album=str(self.album.id))

        self.assertIn("Retagging date tags for Holiday", output)
        self.assertNotIn("Added date tags", output)

    def test_unknown_album_raises(self):
        with self.assertRaises(Album.DoesNotExist):
            self.run_command(COMMAND, album="9999")

    def test_created_tags_land_in_the_date_category(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))

        self.run_command(COMMAND, album=str(self.album.id))

        year_tag = Tag.objects.get(name="2024")
        self.assertEqual(year_tag.tagcategory, self.date_category)
        self.assertIn("2024", self.tags_for(photo))

    def test_redating_a_photo_replaces_rather_than_accumulates_tags(self):
        photo = create_photo(self.album, "a.jpg", make_datetime(2024, 3, 9))
        self.run_command(COMMAND, album=str(self.album.id))

        photo.date = make_datetime(2023, 7, 4)
        photo.save()
        self.run_command(COMMAND, album=str(self.album.id))

        self.assertEqual(self.tags_for(photo), ["2023", "July"])
