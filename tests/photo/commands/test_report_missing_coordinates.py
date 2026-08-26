"""Tests for the ``report_missing_coordinates`` management command.

Read-only report: Location tags with no usable latitude. The interactive
counterpart that actually fills them in is report_get_coordinates.
"""

from django.test import override_settings
from django.urls import reverse

from photo.models import TagCategory
from tests.base import CommandTestCase, create_tag, set_tag_prop

COMMAND = "report_missing_coordinates"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class ReportMissingCoordinatesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.location = TagCategory.objects.create(name="Location")

    def test_a_tag_with_no_latitude_is_reported(self):
        create_tag("Harrogate", self.location)

        output = self.run_command(COMMAND)

        self.assertIn("Harrogate", output)
        self.assertIn("1 missing coordinates", output)

    def test_a_tag_with_a_latitude_is_not_reported(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "53.99")

        output = self.run_command(COMMAND)

        self.assertNotIn("Harrogate", output)
        self.assertIn("OK", output)

    def test_a_zero_latitude_counts_as_missing(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "0")

        output = self.run_command(COMMAND)

        self.assertIn("Harrogate", output)
        self.assertIn("1 missing coordinates", output)

    def test_tags_outside_the_location_category_are_ignored(self):
        people = TagCategory.objects.create(name="People")
        create_tag("Alice", people)
        create_tag("Uncategorised")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_every_missing_tag_is_numbered(self):
        create_tag("Harrogate", self.location)
        create_tag("Leeds", self.location)

        output = self.run_command(COMMAND)

        self.assertIn("1 Harrogate", output)
        self.assertIn("2 Leeds", output)
        self.assertIn("2 missing coordinates", output)

    def test_no_tags_at_all_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Missing coordinates", output)
        self.assertIn("OK", output)

    def test_both_links_are_printed(self):
        tag = create_tag("Harrogate", self.location)

        output = self.run_command(COMMAND)

        domain = "https://photos.example.test"
        self.assertIn(domain + reverse("admin:photo_tag_change", args=(tag.id,)), output)
        self.assertIn(domain + reverse("photo:tag_slug", args=(tag.slug,)), output)

    def test_the_report_does_not_change_anything(self):
        from photo.models import TagProps

        create_tag("Harrogate", self.location)

        self.run_command(COMMAND)

        self.assertEqual(TagProps.objects.count(), 0)

    def test_a_longitude_alone_does_not_satisfy_the_check(self):
        # Only lat is inspected, so a tag with lng but no lat still shows up.
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lng", "-1.54")

        output = self.run_command(COMMAND)

        self.assertIn("Harrogate", output)
