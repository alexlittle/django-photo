"""Tests for the ``integrity_remove_unused_tags`` management command.

Deletes every tag with no photos attached. Destructive and unprompted, in the
same shape as integrity_remove_empty_albums.
"""

from photo.models import Tag, TagCategory, TagProps
from tests.base import CommandTestCase, create_album, create_photo, create_tag, set_tag_prop

COMMAND = "integrity_remove_unused_tags"


class IntegrityRemoveUnusedTagsTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_an_unused_tag_is_deleted(self):
        create_tag("Beach")

        self.run_command(COMMAND)

        self.assertFalse(Tag.objects.filter(name="Beach").exists())

    def test_a_tag_in_use_survives(self):
        beach = create_tag("Beach")
        photo = create_photo(self.album, "a.jpg")
        from tests.base import tag_photo

        tag_photo(photo, beach)

        self.run_command(COMMAND)

        self.assertTrue(Tag.objects.filter(name="Beach").exists())

    def test_only_the_unused_tags_go(self):
        beach = create_tag("Beach")
        create_tag("Unused")
        photo = create_photo(self.album, "a.jpg")
        from tests.base import tag_photo

        tag_photo(photo, beach)

        self.run_command(COMMAND)

        self.assertEqual(list(Tag.objects.values_list("name", flat=True)), ["Beach"])

    def test_deletions_are_reported(self):
        create_tag("Beach")

        output = self.run_command(COMMAND)

        self.assertIn("Removing: Beach", output)
        self.assertIn("1 unused tags removed", output)

    def test_the_count_covers_every_tag_removed(self):
        create_tag("Beach")
        create_tag("Sunset")

        output = self.run_command(COMMAND)

        self.assertIn("2 unused tags removed", output)

    def test_nothing_to_do_reports_ok(self):
        beach = create_tag("Beach")
        photo = create_photo(self.album, "a.jpg")
        from tests.base import tag_photo

        tag_photo(photo, beach)

        output = self.run_command(COMMAND)

        self.assertIn("Unused tags", output)
        self.assertIn("OK", output)

    def test_an_empty_database_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_a_categorised_but_unused_tag_is_still_deleted(self):
        location = TagCategory.objects.create(name="Location")
        create_tag("Harrogate", location)

        self.run_command(COMMAND)

        self.assertFalse(Tag.objects.filter(name="Harrogate").exists())
        self.assertTrue(TagCategory.objects.filter(name="Location").exists())

    def test_deleting_a_tag_discards_its_properties(self):
        # TagProps cascades. For Location tags that means the lat/lng/country
        # gathered through report_get_coordinates -- which is a slow manual
        # process -- goes with the tag. A location that temporarily has no
        # photos loses its geocoding permanently.
        location = TagCategory.objects.create(name="Location")
        harrogate = create_tag("Harrogate", location)
        set_tag_prop(harrogate, "lat", "53.99")
        set_tag_prop(harrogate, "lng", "-1.54")
        set_tag_prop(harrogate, "country", "GB")

        self.run_command(COMMAND)

        self.assertEqual(TagProps.objects.count(), 0)

    def test_the_command_deletes_without_asking(self):
        create_tag("Beach")

        self.run_command(COMMAND)

        self.assertEqual(Tag.objects.count(), 0)
