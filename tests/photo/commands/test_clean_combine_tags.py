"""Tests for the ``clean_combine_tags`` management command.

Takes two tag slugs, repoints every PhotoTag from the old tag to the new one,
then deletes the old tag.
"""

from unittest import expectedFailure

from photo.models import PhotoTag, Tag
from tests.base import CommandTestCase, create_album, create_photo, create_tag, tag_photo

COMMAND = "clean_combine_tags"


class CleanCombineTagsTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.old = create_tag("Seaside")
        self.new = create_tag("Beach")

    def tags_for(self, photo):
        return list(Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True))

    def test_photos_move_to_the_new_tag(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.old)

        self.run_command(COMMAND, "seaside", "beach")

        self.assertEqual(self.tags_for(photo), ["Beach"])

    def test_the_old_tag_is_deleted(self):
        self.run_command(COMMAND, "seaside", "beach")

        self.assertFalse(Tag.objects.filter(slug="seaside").exists())
        self.assertTrue(Tag.objects.filter(slug="beach").exists())

    def test_every_photo_is_moved(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")
        tag_photo(first, self.old)
        tag_photo(second, self.old)

        self.run_command(COMMAND, "seaside", "beach")

        self.assertEqual(self.tags_for(first), ["Beach"])
        self.assertEqual(self.tags_for(second), ["Beach"])

    def test_other_tags_on_the_photo_survive(self):
        sunset = create_tag("Sunset")
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.old, sunset)

        self.run_command(COMMAND, "seaside", "beach")

        self.assertCountEqual(self.tags_for(photo), ["Beach", "Sunset"])

    def test_photos_already_on_the_new_tag_are_left_alone(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.new)

        self.run_command(COMMAND, "seaside", "beach")

        self.assertEqual(self.tags_for(photo), ["Beach"])

    def test_the_number_moved_is_reported(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")
        tag_photo(first, self.old)
        tag_photo(second, self.old)

        output = self.run_command(COMMAND, "seaside", "beach")

        self.assertIn("2 tags replaced seaside", output)

    def test_combining_an_unused_tag_reports_zero(self):
        output = self.run_command(COMMAND, "seaside", "beach")

        self.assertIn("0 tags replaced seaside", output)

    def test_unknown_old_slug_raises(self):
        with self.assertRaises(Tag.DoesNotExist):
            self.run_command(COMMAND, "nope", "beach")

    def test_unknown_new_slug_raises_before_anything_changes(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.old)

        with self.assertRaises(Tag.DoesNotExist):
            self.run_command(COMMAND, "seaside", "nope")

        self.assertEqual(self.tags_for(photo), ["Seaside"])

    def test_a_photo_carrying_both_tags_does_not_end_up_double_tagged(self):
        # PhotoTag now has unique_together on (photo, tag), and the command
        # repoints rows with get_or_create rather than pt.save(). A photo that
        # already had both tags ends up with a single row for the new tag.
        #
        # This used to matter beyond cosmetics: TagSlugView annotates
        # Count("id") over the phototag join and filters on the number of
        # slugs requested, so a doubled row made a single-tag photo match a
        # two-tag query.
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.old, self.new)

        self.run_command(COMMAND, "seaside", "beach")

        self.assertEqual(PhotoTag.objects.filter(photo=photo, tag=self.new).count(), 1)

    @expectedFailure
    def test_combining_a_tag_with_itself_is_refused(self):
        # Both lookups return the same row, so every PhotoTag is repointed to
        # the tag that is then deleted -- cascading the lot away. The photo
        # silently loses the tag entirely.
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.old)

        self.run_command(COMMAND, "seaside", "seaside")

        self.assertEqual(self.tags_for(photo), ["Seaside"])
