"""Tests for the ``tag_diff`` management command.

Flags tags whose names are close matches for other tags -- typo and near-
duplicate detection, via difflib.get_close_matches over every pair.
"""

from django.test import override_settings
from django.urls import reverse

from photo.models import Tag
from tests.base import CommandTestCase, create_tag

COMMAND = "tag_diff"


@override_settings(DOMAIN_NAME="https://photos.example.test", IGNORE_TAG_REGEXS=[])
class TagDiffTests(CommandTestCase):
    def test_similar_tags_are_flagged(self):
        create_tag("Sunset")
        create_tag("Sunsets")

        output = self.run_command(COMMAND)

        self.assertIn("Sunset", output)
        self.assertIn("tags close to others", output)

    def test_dissimilar_tags_are_not_flagged(self):
        create_tag("Beach")
        create_tag("Sunset")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_a_single_tag_has_nothing_to_match(self):
        create_tag("Sunset")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_no_tags_at_all_reports_ok(self):
        output = self.run_command(COMMAND)

        self.assertIn("Tag diff", output)
        self.assertIn("OK", output)

    def test_a_lower_cutoff_catches_looser_matches(self):
        # "Beach"/"Beaches" scores 0.833 -- under the 0.85 default, over 0.8.
        create_tag("Beach")
        create_tag("Beaches")

        strict = self.run_command(COMMAND)
        loose = self.run_command(COMMAND, "0.8")

        self.assertIn("OK", strict)
        self.assertIn("tags close to others", loose)

    def test_a_higher_cutoff_suppresses_matches(self):
        create_tag("Sunset")
        create_tag("Sunsets")

        output = self.run_command(COMMAND, "0.99")

        self.assertIn("OK", output)

    def test_the_default_cutoff_is_applied(self):
        create_tag("Harrogate")
        create_tag("Harrogat")

        output = self.run_command(COMMAND)

        self.assertIn("Harrogat", output)

    def test_ignored_regexes_suppress_a_pair(self):
        create_tag("Sunset")
        create_tag("Sunsets")

        with override_settings(IGNORE_TAG_REGEXS=[r"^Sunset"]):
            output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_a_regex_matching_only_one_of_the_pair_does_not_suppress(self):
        create_tag("Sunset")
        create_tag("Sunsets")

        with override_settings(IGNORE_TAG_REGEXS=[r"^Sunsets$"]):
            output = self.run_command(COMMAND)

        self.assertIn("tags close to others", output)

    def test_a_pair_is_reported_from_both_sides(self):
        # Every tag is compared against every other, so a single near-duplicate
        # pair counts twice and prints twice. Fine at small scale, noisy on a
        # real library.
        create_tag("Sunset")
        create_tag("Sunsets")

        output = self.run_command(COMMAND)

        self.assertIn("2 tags close to others", output)

    def test_at_most_three_matches_are_shown_per_tag(self):
        # difflib.get_close_matches defaults to n=3, so a tag with more near
        # neighbours than that has the rest silently dropped.
        for name in ("Sunset", "Sunsets", "Sunsett", "Sunsetts", "Sunsetted"):
            create_tag(name)

        output = self.run_command(COMMAND)

        first_block = output.split("----------------")[0]
        self.assertLessEqual(first_block.count("Sunset"), 6)

    def test_identically_named_tags_are_invisible(self):
        # Tag.name has no unique constraint, but the comparison list is built
        # from names and filtered with `tag != current_tag`, which removes every
        # copy of the name. So exact duplicates -- arguably the thing most worth
        # finding -- never surface here.
        create_tag("Sunset")
        Tag.objects.create(name="Sunset", slug="sunset-2")

        output = self.run_command(COMMAND)

        self.assertIn("OK", output)

    def test_the_link_uses_the_tags_stored_slug(self):
        # The URL is built from tag.slug rather than slugify(name). Those
        # agree for a freshly created tag, but Tag.save() only derives the
        # slug when it's blank, so a renamed tag keeps its original slug and
        # the link still resolves. The rename (bypassing save(), as a direct
        # DB update would) still has to stay close enough to "Sunsets" to be
        # flagged, otherwise there'd be nothing to assert a link on.
        tag = create_tag("Sunset")
        create_tag("Sunsets")
        Tag.objects.filter(pk=tag.pk).update(name="Sunsete")

        output = self.run_command(COMMAND)

        expected = "https://photos.example.test" + reverse("photo:tag_slug", args=(tag.slug,))
        self.assertIn(expected, output)
        self.assertEqual(tag.slug, "sunset")
