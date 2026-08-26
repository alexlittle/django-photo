"""Tests for the ``integrity_only_one_tag`` management command.

Reports photos carrying fewer than two tags, walking albums in name order.
"""

from unittest import expectedFailure

from django.test import override_settings
from django.urls import reverse

from photo.models import PhotoTag
from tests.base import CommandTestCase, create_album, create_photo, create_tag, tag_photo

COMMAND = "integrity_only_one_tag"


@override_settings(DOMAIN_NAME="https://photos.example.test")
class IntegrityOnlyOneTagTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.beach = create_tag("Beach")
        self.sunset = create_tag("Sunset")

    def test_an_untagged_photo_is_reported(self):
        create_photo(self.album, "a.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/a.jpg", output)
        self.assertIn("1 photos with only one tag", output)

    def test_a_photo_with_one_tag_is_reported(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        output = self.run_command(COMMAND)

        self.assertIn("/2024/a.jpg", output)
        self.assertIn("1 photos with only one tag", output)

    def test_a_photo_with_two_tags_is_not_reported(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach, self.sunset)

        output = self.run_command(COMMAND)

        self.assertNotIn("a.jpg", output)
        self.assertIn("OK", output)

    def test_every_thinly_tagged_photo_is_counted(self):
        first = create_photo(self.album, "a.jpg")
        create_photo(self.album, "b.jpg")
        well_tagged = create_photo(self.album, "c.jpg")
        tag_photo(first, self.beach)
        tag_photo(well_tagged, self.beach, self.sunset)

        output = self.run_command(COMMAND)

        self.assertIn("2 photos with only one tag", output)

    def test_photos_are_gathered_across_albums(self):
        other = create_album("/2023/")
        create_photo(self.album, "a.jpg")
        create_photo(other, "b.jpg")

        output = self.run_command(COMMAND)

        self.assertIn("/2024/a.jpg", output)
        self.assertIn("/2023/b.jpg", output)
        self.assertIn("2 photos with only one tag", output)

    def test_albums_are_walked_in_name_order(self):
        other = create_album("/2023/")
        create_photo(self.album, "a.jpg")
        create_photo(other, "b.jpg")

        output = self.run_command(COMMAND)

        self.assertLess(output.index("/2023/b.jpg"), output.index("/2024/a.jpg"))

    def test_no_photos_at_all_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Photos with only one tag", output)
        self.assertIn("OK", output)

    def test_an_empty_album_contributes_nothing(self):
        create_album("/2023/")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_duplicate_tag_rows_hide_a_thinly_tagged_photo(self):
        # The count is over PhotoTag rows, not distinct tags. PhotoTag has no
        # unique constraint, and clean_combine_tags can leave two rows pointing
        # at the same tag -- which makes a one-tag photo look adequately
        # tagged. Counting distinct tags would be sturdier.
        photo = create_photo(self.album, "a.jpg")
        PhotoTag.objects.create(photo=photo, tag=self.beach)
        PhotoTag.objects.create(photo=photo, tag=self.beach)

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    @expectedFailure
    def test_the_edit_link_is_well_formed(self):
        # Built by hand as f"{DOMAIN_NAME}/photo/edit/{id}", which drops the
        # trailing slash that photo:edit actually uses. That is a third URL
        # style in this command set -- integrity_album_covers uses reverse(),
        # files_deep_structure omits the leading slash, this one omits the
        # trailing one. reverse("photo:edit") would settle it.
        photo = create_photo(self.album, "a.jpg")

        output = self.run_command(COMMAND)

        expected = "https://photos.example.test" + reverse(
            "photo:edit", kwargs={"photo_id": photo.id}
        )
        self.assertIn(expected, output)
