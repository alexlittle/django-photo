"""Tests for the ``integrity_uncategorised_tags`` management command.

Reports tags with no TagCategory set.
"""

from django.test import override_settings
from django.urls import reverse

from photo.models import TagCategory
from tests.base import CommandTestCase, create_album, create_photo, create_tag, make_datetime

COMMAND = "integrity_uncategorised_tags"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class IntegrityUncategorisedTagsTests(CommandTestCase):
    def test_an_uncategorised_tag_is_reported(self):
        create_tag("Beach")

        output = self.run_command(COMMAND)

        self.assertIn("Beach", output)
        self.assertIn("1 uncategorised tags", output)

    def test_a_categorised_tag_is_not_reported(self):
        location = TagCategory.objects.create(name="Location")
        create_tag("Harrogate", location)

        output = self.run_command(COMMAND)

        self.assertNotIn("Harrogate", output)
        self.assertIn("OK", output)

    def test_every_uncategorised_tag_is_counted(self):
        location = TagCategory.objects.create(name="Location")
        create_tag("Beach")
        create_tag("Sunset")
        create_tag("Harrogate", location)

        output = self.run_command(COMMAND)

        self.assertIn("2 uncategorised tags", output)

    def test_no_tags_at_all_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Uncategorised tags", output)
        self.assertIn("OK", output)

    def test_the_link_points_at_the_admin_change_page(self):
        tag = create_tag("Beach")

        output = self.run_command(COMMAND)

        expected = "https://photos.example.test" + reverse("admin:photo_tag_change", args=(tag.id,))
        self.assertIn(expected, output)

    def test_an_unused_uncategorised_tag_is_still_reported(self):
        create_tag("Orphan")

        output = self.run_command(COMMAND)

        self.assertIn("Orphan", output)

    def test_date_tags_created_by_the_retag_commands_show_up_here(self):
        # clean_retag_dates and clean_whatsapp_redate both create year and month
        # tags via get_or_create(name=...) with no tagcategory, so this report
        # steadily fills up with them. Running those commands makes this one
        # noisier rather than the library tidier.
        album = create_album("/2024/", title="Holiday")
        create_photo(album, "a.jpg", make_datetime(2024, 3, 9))
        TagCategory.objects.create(name="Date")

        self.run_command("clean_retag_dates", album=str(album.id))
        output = self.run_command(COMMAND)

        self.assertIn("2024", output)
        self.assertIn("March", output)
        self.assertIn("2 uncategorised tags", output)
