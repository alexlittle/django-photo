"""Tests for the ``integrity_create_slugs`` management command.

Backfills slugs on tag categories and tags that are missing one.

Two independent problems used to stop it doing that:
  * ``slug = models.SlugField()`` is not nullable, so a missing slug is stored
    as "" and ``filter(slug=None)`` (which Django turns into IS NULL) matched
    nothing at all -- the command now filters on ``slug=""`` instead;
  * both models only derived a slug ``if not self.id``, so re-saving an
    existing row never populated it even if the filter did select it -- the
    guard is now ``if not self.slug``, so a blank slug is filled in on any
    save, while a tag that already has a slug keeps it even if renamed.
"""

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

    def test_a_blank_slug_is_repaired_by_resaving(self):
        # save() now guards on `if not self.slug`, so calling save() on an
        # existing row with a blank slug recomputes it. A tag that already
        # has a slug is untouched even if its name changes -- only a blank
        # slug is filled in.
        tag = self.blank_the_slug(create_tag("Beach"))

        tag.save()

        tag.refresh_from_db()
        self.assertEqual(tag.slug, "beach")

    def test_a_blank_slug_is_not_selected_by_the_filter(self):
        # The first half: filter(slug=None) becomes IS NULL, and the column is
        # NOT NULL, so nothing is ever returned.
        self.blank_the_slug(create_tag("Beach"))

        self.assertFalse(Tag.objects.filter(slug=None).exists())
        self.assertTrue(Tag.objects.filter(slug="").exists())

    def test_a_tag_with_a_blank_slug_is_repaired(self):
        tag = self.blank_the_slug(create_tag("Beach"))

        self.run_command(COMMAND)

        tag.refresh_from_db()
        self.assertEqual(tag.slug, "beach")

    def test_a_tag_category_with_a_blank_slug_is_repaired(self):
        category = self.blank_the_slug(TagCategory.objects.create(name="Location"))

        self.run_command(COMMAND)

        category.refresh_from_db()
        self.assertEqual(category.slug, "location")

    def test_repaired_names_are_reported(self):
        self.blank_the_slug(create_tag("Beach"))

        output = self.run_command(COMMAND)

        self.assertIn("Beach", output)
