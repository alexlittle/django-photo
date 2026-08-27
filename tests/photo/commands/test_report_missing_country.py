"""Tests for the ``report_missing_country`` management command.

This one is interactive: for every Location tag with no country property it
prints a couple of links and blocks on ``input()`` for a country code, with "0"
meaning skip. The tests drive it by patching ``builtins.input``.

Note it reverses ``admin:photo_tag_change``, so django.contrib.admin has to be
installed and Tag registered for these to resolve.
"""

from unittest.mock import patch

from django.urls import reverse

from photo.models import TagCategory, TagProps
from tests.base import CommandTestCase, create_tag, set_site_domain, set_tag_prop

COMMAND = "report_missing_country"


class ReportMissingCountryTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        set_site_domain("photos.example.test")
        self.location = TagCategory.objects.create(name="Location")

    def run_with_answers(self, *answers):
        """Run the command, feeding the given replies to input() in order."""
        with patch("builtins.input", side_effect=list(answers)) as prompt:
            output = self.run_command(COMMAND)
        return output, prompt

    def test_a_tag_without_a_country_is_prompted_for(self):
        tag = create_tag("Harrogate", self.location)

        output, prompt = self.run_with_answers("GB")

        self.assertEqual(prompt.call_count, 1)
        self.assertIn("Harrogate", output)
        self.assertEqual(TagProps.objects.get(tag=tag, name="country").value, "GB")

    def test_a_tag_with_a_country_is_skipped(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "country", "GB")

        _output, prompt = self.run_with_answers()

        prompt.assert_not_called()

    def test_a_tag_with_an_empty_country_is_prompted_again(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "country", "")

        _output, prompt = self.run_with_answers("GB")

        self.assertEqual(prompt.call_count, 1)
        self.assertEqual(TagProps.objects.get(tag=tag, name="country").value, "GB")

    def test_zero_skips_without_writing_anything(self):
        tag = create_tag("Harrogate", self.location)

        self.run_with_answers("0")

        self.assertFalse(TagProps.objects.filter(tag=tag, name="country").exists())

    def test_tags_outside_the_location_category_are_ignored(self):
        people = TagCategory.objects.create(name="People")
        create_tag("Alice", people)
        create_tag("Uncategorised")

        _output, prompt = self.run_with_answers()

        prompt.assert_not_called()

    def test_every_tag_missing_a_country_is_visited(self):
        create_tag("Harrogate", self.location)
        create_tag("Leeds", self.location)

        output, prompt = self.run_with_answers("GB", "GB")

        self.assertEqual(prompt.call_count, 2)
        self.assertEqual(TagProps.objects.filter(name="country").count(), 2)
        self.assertIn("1 Harrogate", output)
        self.assertIn("2 Leeds", output)

    def test_answers_are_applied_per_tag(self):
        harrogate = create_tag("Harrogate", self.location)
        paris = create_tag("Paris", self.location)

        self.run_with_answers("GB", "FR")

        # Tag.Meta orders by name, so Harrogate is prompted before Paris.
        self.assertEqual(TagProps.objects.get(tag=harrogate, name="country").value, "GB")
        self.assertEqual(TagProps.objects.get(tag=paris, name="country").value, "FR")

    def test_output_includes_admin_and_public_links(self):
        tag = create_tag("Harrogate", self.location)

        output, _prompt = self.run_with_answers("GB")

        self.assertIn(
            "https://photos.example.test" + reverse("admin:photo_tag_change", args=(tag.id,)),
            output,
        )
        self.assertIn(
            "https://photos.example.test" + reverse("photo:tag_slug", args=(tag.slug,)),
            output,
        )

    def test_nothing_missing_produces_only_the_header(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "country", "GB")

        output, _prompt = self.run_with_answers()

        self.assertIn("Missing countries", output)
        self.assertNotIn("Harrogate", output)

    def test_an_empty_answer_is_treated_as_skip(self):
        tag = create_tag("Harrogate", self.location)

        self.run_with_answers("")

        self.assertFalse(TagProps.objects.filter(tag=tag, name="country").exists())
