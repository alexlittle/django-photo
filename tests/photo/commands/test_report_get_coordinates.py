"""Tests for the ``report_get_coordinates`` management command.

Interactive geocoder: for each Location tag with no usable latitude it queries
GeoNames, prints up to twenty candidates, and prompts for one to accept.

The network call is mocked throughout -- these tests never reach api.geonames.org.
"""

import json
from unittest.mock import patch

from django.test import override_settings

from photo.models import TagCategory, TagProps
from tests.base import CommandTestCase, create_tag, set_tag_prop

COMMAND = "report_get_coordinates"


def geonames(*entries):
    """Build a GeoNames-shaped payload."""
    return {"geonames": list(entries)}


def place(name="Harrogate", lat="53.99", lng="-1.54", country="GB"):
    return {
        "toponymName": name,
        "name": name,
        "adminName1": "England",
        "countryCode": country,
        "lat": lat,
        "lng": lng,
    }


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body


@override_settings(GEONAMES_USERNAME="testuser")
class ReportGetCoordinatesTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.location = TagCategory.objects.create(name="Location")

    def run_with(self, payload, *answers):
        with (
            patch("urllib.request.urlopen", return_value=FakeResponse(payload)) as urlopen,
            patch("builtins.input", side_effect=list(answers)) as prompt,
        ):
            output = self.run_command(COMMAND)
        return output, urlopen, prompt

    def test_accepting_a_result_stores_lat_lng_and_country(self):
        tag = create_tag("Harrogate", self.location)

        self.run_with(geonames(place()), "0")

        self.assertEqual(TagProps.objects.get(tag=tag, name="lat").value, "53.99")
        self.assertEqual(TagProps.objects.get(tag=tag, name="lng").value, "-1.54")
        self.assertEqual(TagProps.objects.get(tag=tag, name="country").value, "GB")

    def test_a_later_candidate_can_be_chosen(self):
        tag = create_tag("Harrogate", self.location)
        payload = geonames(place(), place(name="Harrogate TN", lat="35.9", country="US"))

        self.run_with(payload, "1")

        self.assertEqual(TagProps.objects.get(tag=tag, name="lat").value, "35.9")
        self.assertEqual(TagProps.objects.get(tag=tag, name="country").value, "US")

    def test_ignore_leaves_the_tag_alone(self):
        tag = create_tag("Harrogate", self.location)

        output, _urlopen, _prompt = self.run_with(geonames(place()), "i")

        self.assertFalse(TagProps.objects.filter(tag=tag).exists())
        self.assertIn("ignoring", output)

    def test_no_leaves_the_tag_alone(self):
        tag = create_tag("Harrogate", self.location)

        output, _urlopen, _prompt = self.run_with(geonames(place()), "n")

        self.assertFalse(TagProps.objects.filter(tag=tag).exists())
        self.assertIn("no", output)

    def test_a_tag_with_coordinates_is_skipped(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "53.99")

        _output, urlopen, prompt = self.run_with(geonames(place()))

        urlopen.assert_not_called()
        prompt.assert_not_called()

    def test_a_tag_with_a_zero_latitude_is_retried(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "0")

        self.run_with(geonames(place()), "0")

        self.assertEqual(TagProps.objects.get(tag=tag, name="lat").value, "53.99")

    def test_tags_outside_the_location_category_are_ignored(self):
        people = TagCategory.objects.create(name="People")
        create_tag("Alice", people)
        create_tag("Uncategorised")

        _output, urlopen, prompt = self.run_with(geonames(place()))

        urlopen.assert_not_called()
        prompt.assert_not_called()

    def test_an_empty_result_set_does_not_prompt(self):
        tag = create_tag("Harrogate", self.location)

        _output, urlopen, prompt = self.run_with(geonames())

        urlopen.assert_called_once()
        prompt.assert_not_called()
        self.assertFalse(TagProps.objects.filter(tag=tag).exists())

    def test_the_query_carries_the_tag_name_and_username(self):
        create_tag("Harrogate", self.location)

        _output, urlopen, _prompt = self.run_with(geonames(place()), "0")

        url = urlopen.call_args.args[0].full_url
        self.assertIn("q=Harrogate", url)
        self.assertIn("username=testuser", url)
        self.assertIn("maxRows=20", url)

    def test_a_known_country_narrows_the_query(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "country", "GB")

        _output, urlopen, _prompt = self.run_with(geonames(place()), "0")

        self.assertIn("country=GB", urlopen.call_args.args[0].full_url)

    def test_a_tag_without_a_country_does_not_send_one(self):
        create_tag("Harrogate", self.location)

        _output, urlopen, _prompt = self.run_with(geonames(place()), "0")

        self.assertNotIn("country=", urlopen.call_args.args[0].full_url)

    def test_existing_properties_are_updated_not_duplicated(self):
        tag = create_tag("Harrogate", self.location)
        set_tag_prop(tag, "lat", "0")
        set_tag_prop(tag, "country", "GB")

        self.run_with(geonames(place()), "0")

        self.assertEqual(TagProps.objects.filter(tag=tag, name="lat").count(), 1)
        self.assertEqual(TagProps.objects.filter(tag=tag, name="country").count(), 1)

    def test_candidates_are_listed_for_the_user(self):
        create_tag("Harrogate", self.location)

        output, _urlopen, _prompt = self.run_with(geonames(place()), "0")

        self.assertIn("Harrogate", output)
        self.assertIn("England", output)
        self.assertIn("GB", output)

    def test_each_pending_tag_is_visited(self):
        create_tag("Harrogate", self.location)
        create_tag("Leeds", self.location)

        _output, urlopen, prompt = self.run_with(geonames(place()), "0", "0")

        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(prompt.call_count, 2)

    def test_a_non_numeric_answer_is_handled(self):
        tag = create_tag("Harrogate", self.location)

        output, _urlopen, _prompt = self.run_with(geonames(place()), "")

        self.assertIn("invalid selection", output)
        self.assertFalse(TagProps.objects.filter(tag=tag).exists())

    def test_an_out_of_range_answer_is_handled(self):
        tag = create_tag("Harrogate", self.location)

        output, _urlopen, _prompt = self.run_with(geonames(place()), "5")

        self.assertIn("invalid selection", output)
        self.assertFalse(TagProps.objects.filter(tag=tag).exists())

    def test_a_geonames_error_response_is_handled(self):
        # GeoNames returns {"status": {...}} rather than a geonames key when a
        # daily limit is hit or credentials are wrong.
        tag = create_tag("Harrogate", self.location)

        output, _urlopen, prompt = self.run_with(
            {"status": {"message": "daily limit exceeded", "value": 18}}
        )

        self.assertIn("GeoNames error", output)
        prompt.assert_not_called()
        self.assertFalse(TagProps.objects.filter(tag=tag).exists())
