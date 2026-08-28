"""Tests for ``photo.lib``.

``get_exif``, ``ignore_folder`` and ``ignore_file`` are pure/near-pure
functions. ``add_tags`` and ``rename_photo_file`` touch the database (and,
for renaming, the filesystem). ``add_or_update_xmp_metadata`` drives libxmp
against a real file on disk -- the XMP objects themselves are patched here so
the assertions describe the logic (what gets written and when) rather than
exempi's behaviour.
"""

import os
from unittest.mock import MagicMock, patch

from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from photo.lib import (
    add_or_update_xmp_metadata,
    add_tags,
    get_domain,
    get_exif,
    ignore_file,
    ignore_folder,
    rename_photo_file,
)
from photo.models import PhotoTag, Tag, TagCategory, TagProps
from tests.base import PhotoRootTestCase, create_album, create_photo, create_tag, tag_photo


class GetDomainTests(TestCase):
    def test_builds_an_https_url_from_the_configured_site(self):
        Site.objects.update_or_create(
            pk=1, defaults={"domain": "example.com", "name": "example.com"}
        )

        self.assertEqual(get_domain(), "https://example.com")

    def test_reflects_a_changed_site_domain(self):
        Site.objects.update_or_create(pk=1, defaults={"domain": "old.example", "name": "old"})
        Site.objects.filter(pk=1).update(domain="new.example")

        self.assertEqual(get_domain(), "https://new.example")


class GetExifTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_returns_the_decoded_tags_and_true_when_exif_is_present(self):
        photo = create_photo(self.album, "a.jpg")
        path = self.write_image_with_exif(photo, **{"306": "2024:01:01 12:00:00"})

        exif, found = get_exif(path)

        self.assertTrue(found)
        self.assertEqual(exif["DateTime"], "2024:01:01 12:00:00")

    def test_returns_none_and_false_when_there_is_no_exif_data(self):
        photo = create_photo(self.album, "a.jpg")
        path = self.write_image(photo)

        exif, found = get_exif(path)

        self.assertIsNone(exif)
        self.assertFalse(found)


class IgnoreFolderTests(TestCase):
    def test_a_folder_matching_a_configured_pattern_is_ignored(self):
        with override_settings(IGNORE_FOLDERS=[r".*/\.thumbnails"]):
            self.assertTrue(ignore_folder("/photos/2024/.thumbnails"))

    def test_a_folder_matching_no_pattern_is_not_ignored(self):
        with override_settings(IGNORE_FOLDERS=[r".*/\.thumbnails"]):
            self.assertFalse(ignore_folder("/photos/2024"))

    def test_no_configured_patterns_means_nothing_is_ignored(self):
        with override_settings(IGNORE_FOLDERS=[]):
            self.assertFalse(ignore_folder("/photos/2024"))

    def test_matching_uses_a_leading_match_not_a_full_match(self):
        # re.match only anchors at the start, so a pattern without $ matches
        # any string starting with it.
        with override_settings(IGNORE_FOLDERS=[r"/photos"]):
            self.assertTrue(ignore_folder("/photos/2024/anything"))


class IgnoreFileTests(TestCase):
    def test_a_file_with_a_configured_extension_is_ignored(self):
        with override_settings(IGNORE_EXTENSIONS=[".db", ".tmp"]):
            self.assertTrue(ignore_file("thumbs.db"))

    def test_matching_is_case_insensitive(self):
        with override_settings(IGNORE_EXTENSIONS=[".db"]):
            self.assertTrue(ignore_file("Thumbs.DB"))

    def test_a_file_with_no_matching_extension_is_not_ignored(self):
        with override_settings(IGNORE_EXTENSIONS=[".db"]):
            self.assertFalse(ignore_file("a.jpg"))

    def test_no_configured_extensions_means_nothing_is_ignored(self):
        with override_settings(IGNORE_EXTENSIONS=[]):
            self.assertFalse(ignore_file("thumbs.db"))


class AddTagsTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.photo = create_photo(create_album("/2024/"), "a.jpg")

    def test_an_empty_string_does_nothing_and_returns_false(self):
        result = add_tags(self.photo, "")

        self.assertFalse(result)
        self.assertEqual(PhotoTag.objects.filter(photo=self.photo).count(), 0)

    def test_none_does_nothing_and_returns_false(self):
        result = add_tags(self.photo, None)

        self.assertFalse(result)

    def test_a_single_tag_is_created_and_linked(self):
        add_tags(self.photo, "Beach")

        self.assertEqual(Tag.objects.filter(name="Beach").count(), 1)
        self.assertTrue(PhotoTag.objects.filter(photo=self.photo, tag__name="Beach").exists())

    def test_multiple_comma_separated_tags_are_all_linked(self):
        add_tags(self.photo, "Beach, Holiday, Sun")

        linked = set(Tag.objects.filter(phototag__photo=self.photo).values_list("name", flat=True))
        self.assertEqual(linked, {"Beach", "Holiday", "Sun"})

    def test_surrounding_whitespace_is_stripped_from_each_tag(self):
        add_tags(self.photo, "  Beach  ,  Sun ")

        self.assertTrue(Tag.objects.filter(name="Beach").exists())
        self.assertTrue(Tag.objects.filter(name="Sun").exists())

    def test_blank_entries_between_commas_are_skipped(self):
        add_tags(self.photo, "Beach,,Sun")

        self.assertEqual(PhotoTag.objects.filter(photo=self.photo).count(), 2)

    def test_an_existing_tag_is_reused_rather_than_duplicated(self):
        existing = create_tag("Beach")

        add_tags(self.photo, "Beach")

        self.assertEqual(Tag.objects.filter(name="Beach").count(), 1)
        self.assertTrue(PhotoTag.objects.filter(photo=self.photo, tag=existing).exists())

    def test_linking_the_same_tag_twice_does_not_duplicate_the_link(self):
        tag = create_tag("Beach")
        tag_photo(self.photo, tag)

        add_tags(self.photo, "Beach")

        self.assertEqual(PhotoTag.objects.filter(photo=self.photo, tag=tag).count(), 1)


class RenamePhotoFileTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_renames_the_file_on_disk_and_updates_the_photo(self):
        photo = create_photo(self.album, "a.jpg")
        old_path = self.write_image(photo)

        rename_photo_file(photo)

        self.assertEqual(photo.file, f"a-{photo.id}.jpg")
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(self.image_path(photo)))

    def test_running_twice_is_idempotent(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)

        rename_photo_file(photo)
        first_name = photo.file
        rename_photo_file(photo)

        self.assertEqual(first_name, f"a-{photo.id}.jpg")
        self.assertEqual(photo.file, f"a-{photo.id}.jpg")
        self.assertTrue(os.path.exists(self.image_path(photo)))

    def test_a_missing_file_leaves_the_photo_record_untouched(self):
        photo = create_photo(self.album, "ghost.jpg")

        rename_photo_file(photo)

        photo.refresh_from_db()
        self.assertEqual(photo.file, "ghost.jpg")

    def test_the_suffix_is_inserted_before_the_extension(self):
        photo = create_photo(self.album, "my.holiday.jpg")
        self.write_image(photo)

        rename_photo_file(photo)

        self.assertEqual(photo.file, f"my.holiday-{photo.id}.jpg")


class AddOrUpdateXmpMetadataTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.photo = create_photo(self.album, "a.jpg", title="On the pier")
        self.write_image(self.photo)

    def patched(self, xmp=None):
        xmpfile = MagicMock()
        xmpfile.get_xmp.return_value = xmp
        xmpfile.can_put_xmp.return_value = True
        return patch("photo.lib.XMPFiles", return_value=xmpfile), xmpfile

    def test_writes_the_title_and_tags_into_the_subject_property(self):
        tag = create_tag("Beach")
        tag_photo(self.photo, tag)
        patcher, xmpfile = self.patched()

        with patcher, patch("photo.lib.XMPMeta") as xmp_meta_cls:
            add_or_update_xmp_metadata(self.photo)

        xmp = xmp_meta_cls.return_value
        xmp.append_array_item.assert_called_once()
        desc = xmp.append_array_item.call_args.args[2]
        self.assertEqual(desc, "On the pier - Beach")
        xmpfile.put_xmp.assert_called_once_with(xmp)

    def test_reuses_an_existing_xmp_object_when_the_file_already_has_one(self):
        patcher, xmpfile = self.patched()
        existing_xmp = MagicMock()
        xmpfile.get_xmp.return_value = existing_xmp

        with patcher, patch("photo.lib.XMPMeta") as xmp_meta_cls:
            add_or_update_xmp_metadata(self.photo)

        xmp_meta_cls.assert_not_called()
        existing_xmp.delete_property.assert_called_once()
        xmpfile.put_xmp.assert_called_once_with(existing_xmp)

    def test_location_is_prepended_when_the_photo_has_coordinates(self):
        location_category = TagCategory.objects.create(name="Location", slug="location")
        place = Tag.objects.create(name="Brighton", tagcategory=location_category)
        TagProps.objects.create(tag=place, name="lat", value="50.8")
        TagProps.objects.create(tag=place, name="lng", value="-0.1")
        tag_photo(self.photo, place)
        patcher, _xmpfile = self.patched()

        with patcher, patch("photo.lib.XMPMeta") as xmp_meta_cls:
            add_or_update_xmp_metadata(self.photo)

        desc = xmp_meta_cls.return_value.append_array_item.call_args.args[2]
        self.assertTrue(desc.startswith("(50.8,-0.1), "))

    def test_no_location_is_added_when_the_photo_has_no_location_tag(self):
        patcher, _xmpfile = self.patched()

        with patcher, patch("photo.lib.XMPMeta") as xmp_meta_cls:
            add_or_update_xmp_metadata(self.photo)

        desc = xmp_meta_cls.return_value.append_array_item.call_args.args[2]
        self.assertFalse(desc.startswith("("))

    def test_put_xmp_is_skipped_when_the_file_cannot_be_written(self):
        patcher, xmpfile = self.patched()
        xmpfile.can_put_xmp.return_value = False

        with patcher, patch("photo.lib.XMPMeta"):
            add_or_update_xmp_metadata(self.photo)

        xmpfile.put_xmp.assert_not_called()

    def test_a_missing_file_is_handled_without_raising(self):
        photo = create_photo(self.album, "ghost.jpg")

        with patch("photo.lib.XMPFiles", side_effect=FileNotFoundError):
            add_or_update_xmp_metadata(photo)  # should not raise

    def test_an_unexpected_error_is_swallowed(self):
        with patch("photo.lib.XMPFiles", side_effect=RuntimeError("boom")):
            add_or_update_xmp_metadata(self.photo)  # should not raise

    def test_the_file_handle_is_always_closed(self):
        patcher, xmpfile = self.patched()

        with patcher, patch("photo.lib.XMPMeta"):
            add_or_update_xmp_metadata(self.photo)

        xmpfile.close_file.assert_called_once()

    def test_the_file_handle_is_closed_even_when_writing_fails(self):
        patcher, xmpfile = self.patched()
        xmpfile.can_put_xmp.side_effect = RuntimeError("boom")

        with patcher, patch("photo.lib.XMPMeta"):
            add_or_update_xmp_metadata(self.photo)  # should not raise

        xmpfile.close_file.assert_called_once()
