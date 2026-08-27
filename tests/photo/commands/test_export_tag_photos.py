"""Tests for the ``export_tag_photos`` management command.

Copies every photo carrying a tag (or all of several "+"-joined tags) into an
export directory. With no destination given it creates one under PHOTO_ROOT.
"""

import os

from tests.base import CommandTestCase, create_album, create_photo, create_tag, tag_photo

COMMAND = "export_tag_photos"


class ExportTagPhotosTests(CommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.beach = create_tag("Beach")
        self.sunset = create_tag("Sunset")

    def destination(self):
        path = os.path.join(self.photo_root, "destination")
        os.makedirs(path, exist_ok=True)
        return path

    def test_tagged_photos_are_copied_to_the_given_path(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)
        target = self.destination()

        self.run_command(COMMAND, "beach", target)

        self.assertTrue(os.path.exists(os.path.join(target, "a.jpg")))

    def test_untagged_photos_are_not_copied(self):
        tagged = create_photo(self.album, "a.jpg")
        untagged = create_photo(self.album, "b.jpg")
        self.write_image(tagged)
        self.write_image(untagged)
        tag_photo(tagged, self.beach)
        target = self.destination()

        self.run_command(COMMAND, "beach", target)

        self.assertEqual(os.listdir(target), ["a.jpg"])

    def test_the_original_is_left_in_place(self):
        photo = create_photo(self.album, "a.jpg")
        original = self.write_image(photo)
        tag_photo(photo, self.beach)

        self.run_command(COMMAND, "beach", self.destination())

        self.assertTrue(os.path.exists(original))

    def test_multiple_slugs_require_all_tags(self):
        both = create_photo(self.album, "both.jpg")
        one = create_photo(self.album, "one.jpg")
        self.write_image(both)
        self.write_image(one)
        tag_photo(both, self.beach, self.sunset)
        tag_photo(one, self.beach)
        target = self.destination()

        self.run_command(COMMAND, "beach+sunset", target)

        self.assertEqual(os.listdir(target), ["both.jpg"])

    def test_photos_are_gathered_across_albums(self):
        other = create_album("/2023/")
        first = create_photo(self.album, "a.jpg")
        second = create_photo(other, "b.jpg")
        self.write_image(first)
        self.write_image(second)
        tag_photo(first, self.beach)
        tag_photo(second, self.beach)
        target = self.destination()

        self.run_command(COMMAND, "beach", target)

        self.assertCountEqual(os.listdir(target), ["a.jpg", "b.jpg"])

    def test_without_a_path_a_directory_is_created_under_photo_root(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)

        self.run_command(COMMAND, "beach")

        expected = os.path.join(self.photo_root, "export", "beach")
        self.assertTrue(os.path.exists(os.path.join(expected, "a.jpg")))

    def test_the_export_directory_is_created_inside_photo_root(self):
        # Worth being aware of: the default destination sits under PHOTO_ROOT,
        # so a later `files_scan_photos --files` will walk into it and report
        # every exported copy as missing from the database unless the path is
        # covered by IGNORE_FOLDERS.
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)

        self.run_command(COMMAND, "beach")

        self.assertTrue(os.path.isdir(os.path.join(self.photo_root, "export")))

    def test_reusing_an_existing_default_directory_reports_and_continues(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)
        os.makedirs(os.path.join(self.photo_root, "export", "beach"))

        output = self.run_command(COMMAND, "beach")

        self.assertIn("couldn't create directory", output)
        self.assertTrue(os.path.exists(os.path.join(self.photo_root, "export", "beach", "a.jpg")))

    def test_an_unknown_slug_copies_nothing(self):
        target = self.destination()

        self.run_command(COMMAND, "nope", target)

        self.assertEqual(os.listdir(target), [])

    def test_a_slug_with_no_photos_copies_nothing(self):
        target = self.destination()

        self.run_command(COMMAND, "beach", target)

        self.assertEqual(os.listdir(target), [])

    def test_a_missing_source_file_is_skipped(self):
        ghost = create_photo(self.album, "ghost.jpg")
        real = create_photo(self.album, "a.jpg")
        self.write_image(real)
        tag_photo(ghost, self.beach)
        tag_photo(real, self.beach)
        target = self.destination()

        self.run_command(COMMAND, "beach", target)

        self.assertEqual(os.listdir(target), ["a.jpg"])

    def test_a_destination_that_does_not_exist_is_created(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)
        target = os.path.join(self.photo_root, "nowhere")

        self.run_command(COMMAND, "beach", target)

        self.assertTrue(os.path.exists(os.path.join(target, "a.jpg")))
