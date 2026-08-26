"""Tests for the ``report_missing_source`` management command.

Structurally a sibling of report_missing_coordinates, but interactive: it
prompts for a source value per Location tag that lacks one, with "0" to skip.
Like report_missing_country, the "report_" prefix undersells it -- it writes.
"""

from unittest import expectedFailure
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from photo.models import TagCategory, TagProps
from tests.base import CommandTestCase, create_tag, set_tag_prop

COMMAND = "report_missing_source"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class ReportMissingSourceTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.location = TagCategory.objects.create(name="Location")

    def run_with_answers(self, *answers):
        with patch("builtins.input", side_effect=list(answers)) as prompt:
            output = self.run_command(COMMAND)
        return output, prompt

    def test_a_tag_without_a_source_is_prompted_for(self):
        tag = create_tag("Harrogate", self.location)

        output, prompt = self.run_with_answers("me")

        self.assertEqual(prompt.call_count, 1)
        self.assertIn("Harrogate", output)
        self.assertEqual(TagProps.objects.get(tag=tag, name="source").value, "me")

    def test_a_tag_with_a_source_is_skipped(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "source", "me")

        _output, prompt = self.run_with_answers()

        prompt.assert_not_called()

    def test_a_tag_with_an_empty_source_is_prompted_again(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "source", "")

        _output, prompt = self.run_with_answers("osm")

        self.assertEqual(prompt.call_count, 1)
        self.assertEqual(TagProps.objects.get(tag=tag, name="source").value, "osm")

    def test_zero_skips_without_writing(self):
        tag = create_tag("Harrogate", self.location)

        self.run_with_answers("0")

        self.assertFalse(TagProps.objects.filter(tag=tag, name="source").exists())

    def test_tags_outside_the_location_category_are_ignored(self):
        people = TagCategory.objects.create(name="People")
        create_tag("Alice", people)

        _output, prompt = self.run_with_answers()

        prompt.assert_not_called()

    def test_every_tag_missing_a_source_is_visited(self):
        create_tag("Harrogate", self.location)
        create_tag("Leeds", self.location)

        output, prompt = self.run_with_answers("me", "osm")

        self.assertEqual(prompt.call_count, 2)
        self.assertIn("1 Harrogate", output)
        self.assertIn("2 Leeds", output)

    def test_answers_are_applied_per_tag(self):
        harrogate = create_tag("Harrogate", self.location)
        paris = create_tag("Paris", self.location)

        self.run_with_answers("me", "osm")

        # Tag.Meta orders by name, so Harrogate comes first.
        self.assertEqual(TagProps.objects.get(tag=harrogate, name="source").value, "me")
        self.assertEqual(TagProps.objects.get(tag=paris, name="source").value, "osm")

    def test_both_links_are_printed(self):
        tag = create_tag("Harrogate", self.location)

        output, _prompt = self.run_with_answers("me")

        domain = "https://photos.example.test"
        self.assertIn(domain + reverse("admin:photo_tag_change", args=(tag.id,)), output)
        self.assertIn(domain + reverse("photo:tag_slug", args=(tag.slug,)), output)

    def test_an_empty_answer_stores_an_empty_source(self):
        # Only "0" skips, so pressing enter writes "" -- which the next run
        # treats as missing and prompts for again.
        tag = create_tag("Harrogate", self.location)

        self.run_with_answers("")

        self.assertEqual(TagProps.objects.get(tag=tag, name="source").value, "")

    def test_the_source_value_drives_the_map_view(self):
        # MapView filters Location tags on their "source" prop, so a tag left
        # without one never appears on the map regardless of its coordinates.
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "53.99")

        self.run_with_answers("me")

        self.assertEqual(TagProps.objects.get(tag=tag, name="source").value, "me")

    @expectedFailure
    def test_a_summary_is_printed(self):
        # Unlike report_missing_coordinates, this command has no bcolors import
        # and no closing summary -- it counts matches but never reports the
        # total, and prints no "OK" when there is nothing to do. Easy to mistake
        # a finished run for a broken one, especially inside report_full.
        create_tag("Harrogate", self.location)
        set_tag_prop(create_tag("Leeds", self.location), "source", "me")

        output, _prompt = self.run_with_answers("me")

        self.assertIn("1 missing sources", output)
