"""Tests for the ``integrity_create_slugs`` management command.

Meant to backfill slugs on tag categories and tags that are missing one.

Two independent problems stop it doing that, both covered below:
  * ``slug = models.SlugField()`` is not nullable, so a missing slug is stored
    as "" and ``filter(slug=None)`` (which Django turns into IS NULL) matches
    nothing at all;
  * both models only derive a slug ``if not self.id``, so re-saving an existing
    row would not populate it even if the filter did select it.

The reachable behaviour is therefore "does nothing, quietly". These tests pin
that, and the expected failures describe the intended behaviour.
"""

from unittest import expectedFailure

from photo.models import Tag, TagCategory
from tests.base import CommandTestCase, create_tag

COMMAND = "integrity_create_slugs"


class IntegrityCreateSlugsTests(CommandTestCase):
    def blank_the_slug(self, instance):
        """Clear a slug without going through save(), which would refuse."""
        type(instance).objects.filter(pk=instance.pk).update(slug="")
        instance.refresh_from_db()
        return instance

    def test_running_against_an_empty_database_is_quiet(self):
        output = self.run_command(COMMAND)

        self.assertEqual(output.strip(), "")

    def test_tags_that_already_have_slugs_are_left_alone(self):
        tag = create_tag("Beach")

        self.run_command(COMMAND)

        tag.refresh_from_db()
        self.assertEqual(tag.slug, "beach")

    def test_slugs_are_derived_on_first_save(self):
        # This is where slugs actually come from today -- the model's save(),
        # not this command.
        category = TagCategory.objects.create(name="Tag Category")

        self.assertEqual(category.slug, "tag-category")

    def test_a_blank_slug_cannot_be_repaired_by_resaving(self):
        # The second half of the problem: save() guards on `if not self.id`, so
        # calling save() on an existing row never recomputes the slug.
        tag = self.blank_the_slug(create_tag("Beach"))

        tag.save()

        tag.refresh_from_db()
        self.assertEqual(tag.slug, "")

    def test_a_blank_slug_is_not_selected_by_the_filter(self):
        # The first half: filter(slug=None) becomes IS NULL, and the column is
        # NOT NULL, so nothing is ever returned.
        self.blank_the_slug(create_tag("Beach"))

        self.assertFalse(Tag.objects.filter(slug=None).exists())
        self.assertTrue(Tag.objects.filter(slug="").exists())

    @expectedFailure
    def test_a_tag_with_a_blank_slug_is_repaired(self):
        tag = self.blank_the_slug(create_tag("Beach"))

        self.run_command(COMMAND)

        tag.refresh_from_db()
        self.assertEqual(tag.slug, "beach")

    @expectedFailure
    def test_a_tag_category_with_a_blank_slug_is_repaired(self):
        category = self.blank_the_slug(TagCategory.objects.create(name="Location"))

        self.run_command(COMMAND)

        category.refresh_from_db()
        self.assertEqual(category.slug, "location")

    @expectedFailure
    def test_repaired_names_are_reported(self):
        self.blank_the_slug(create_tag("Beach"))

        output = self.run_command(COMMAND)

        self.assertIn("Beach", output)
