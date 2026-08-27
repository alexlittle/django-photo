"""Tests for ``photo.export.create_album``.

This is the module behind the ``export_pdf_album`` command. It builds a PDF from
either an album or a tag and writes it to PHOTO_ROOT/albums/<name>.pdf.

``Photo.get_thumbnail(size)`` is a real model method backed by sorl-thumbnail.
It's patched here with a fixed return value so the tests don't need real
thumbnail generation or a real MEDIA_ROOT layout.
"""

import os
from unittest.mock import patch

from django.test import override_settings
from PIL import Image as PILImage

from photo.export.create_album import make, make_font_tag
from photo.models import Photo
from tests.base import (
    PhotoRootTestCase,
    create_album,
    create_photo,
    create_tag,
    make_datetime,
    set_photo_prop,
    tag_photo,
)


class MakeFontTagTests(PhotoRootTestCase):
    def test_wraps_text_in_a_sized_font_tag(self):
        self.assertEqual(make_font_tag(40, "Holiday"), "<font size=40>Holiday</font>")

    def test_the_size_is_not_quoted(self):
        # reportlab accepts the unquoted form, but it means a size containing a
        # space would produce broken markup.
        self.assertIn("size=12>", make_font_tag(12, "x"))

    def test_text_is_escaped(self):
        # Album/tag/photo titles reach the paragraph markup through here, so
        # this is what stops a stray < or & from breaking the PDF build.
        self.assertEqual(make_font_tag(20, "Fish & Chips"), "<font size=20>Fish &amp; Chips</font>")

    def test_an_unmatched_markup_character_is_rendered_literally(self):
        self.assertEqual(make_font_tag(20, "<b>Brighton"), "<font size=20>&lt;b&gt;Brighton</font>")


class CreateAlbumTestCase(PhotoRootTestCase):
    """Shared scaffolding: a real thumbnail on disk and an albums/ output dir."""

    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self.photo_root, "albums"), exist_ok=True)

        # get_thumbnail returns a path with a leading slash that the module
        # strips, joined against MEDIA_ROOT/.. -- so build a matching layout.
        self.media_parent = os.path.join(self.photo_root, "media_parent")
        os.makedirs(os.path.join(self.media_parent, "media"), exist_ok=True)
        self.thumbnail = os.path.join(self.media_parent, "thumb.jpg")
        PILImage.new("RGB", (60, 40), (10, 20, 30)).save(self.thumbnail, "JPEG")

        overrides = override_settings(MEDIA_ROOT=os.path.join(self.media_parent, "media"))
        overrides.enable()
        self.addCleanup(overrides.disable)

    def build(self, **kwargs):
        with patch.object(Photo, "get_thumbnail", create=True, return_value="/thumb.jpg"):
            return make(**kwargs)

    def build_capturing_photos(self, **kwargs):
        """Return (path, [photos the build actually rendered])."""
        rendered = []

        def fake_thumbnail(photo, _size):
            # Patched in as a plain function so it binds as a method and we can
            # see which Photo each call was for.
            rendered.append(photo)
            return "/thumb.jpg"

        with patch.object(Photo, "get_thumbnail", fake_thumbnail, create=True):
            path = make(**kwargs)
        return path, rendered


class TagExportTests(CreateAlbumTestCase):
    """The tag path is the one that works."""

    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/", title="Holiday")
        self.beach = create_tag("Beach")

    def test_a_pdf_is_written_and_its_path_returned(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        self.assertEqual(path, os.path.join(self.photo_root, "albums", "Beach.pdf"))
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

    def test_the_file_is_a_pdf(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        with open(path, "rb") as handle:
            self.assertEqual(handle.read(5), b"%PDF-")

    def test_tagged_photos_are_rendered(self):
        tagged = create_photo(self.album, "tagged.jpg")
        create_photo(self.album, "untagged.jpg")
        tag_photo(tagged, self.beach)

        _path, rendered = self.build_capturing_photos(tag_id=self.beach.id)

        self.assertEqual([p.file for p in rendered], ["tagged.jpg"])

    def test_photos_are_gathered_across_albums(self):
        other = create_album("/2023/", title="Other")
        first = create_photo(self.album, "a.jpg")
        second = create_photo(other, "b.jpg")
        tag_photo(first, self.beach)
        tag_photo(second, self.beach)

        _path, rendered = self.build_capturing_photos(tag_id=self.beach.id)

        self.assertCountEqual([p.file for p in rendered], ["a.jpg", "b.jpg"])

    def test_photos_are_rendered_in_date_order(self):
        later = create_photo(self.album, "later.jpg", make_datetime(2024, 6, 1))
        earlier = create_photo(self.album, "earlier.jpg", make_datetime(2024, 1, 1))
        tag_photo(later, self.beach)
        tag_photo(earlier, self.beach)

        _path, rendered = self.build_capturing_photos(tag_id=self.beach.id)

        self.assertEqual([p.file for p in rendered], ["earlier.jpg", "later.jpg"])

    def test_photos_flagged_for_exclusion_are_left_out(self):
        keep = create_photo(self.album, "keep.jpg")
        drop = create_photo(self.album, "drop.jpg")
        tag_photo(keep, self.beach)
        tag_photo(drop, self.beach)
        set_photo_prop(drop, "exclude.album.export", "true")

        _path, rendered = self.build_capturing_photos(tag_id=self.beach.id)

        self.assertEqual([p.file for p in rendered], ["keep.jpg"])

    def test_a_tag_with_no_photos_still_produces_a_pdf(self):
        path = self.build(tag_id=self.beach.id)

        self.assertTrue(os.path.exists(path))

    def test_the_filename_comes_from_the_tag_name(self):
        path = self.build(tag_id=self.beach.id)

        self.assertTrue(path.endswith("Beach.pdf"))

    def test_an_unknown_tag_id_fails_cleanly(self):
        self.assertIsNone(self.build(tag_id=9999))


class AlbumExportTests(CreateAlbumTestCase):
    """The album path renders every photo in the album, tagged or not."""

    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/", title="Holiday")

    def test_an_album_export_contains_the_albums_photos(self):
        # The command used to build two queries unconditionally: an album
        # query, then a tag query that overwrote it before Tag.objects.get
        # raised for the missing tag_id. That threw away the album's own
        # selection on every call. The tag query now only runs when tag_id
        # is actually given.
        photo = create_photo(self.album, "in_album.jpg")
        tag_photo(photo, create_tag("Beach"))

        _path, rendered = self.build_capturing_photos(album_id=self.album.id)

        self.assertEqual([p.file for p in rendered], ["in_album.jpg"])

    def test_an_untagged_photo_in_the_album_is_still_rendered(self):
        # Album membership, not tagging, is what selects photos for the
        # album path -- an untagged photo belongs in its own album's export.
        create_photo(self.album, "untagged.jpg")

        _path, rendered = self.build_capturing_photos(album_id=self.album.id)

        self.assertEqual([p.file for p in rendered], ["untagged.jpg"])

    def test_an_album_export_excludes_photos_from_other_albums(self):
        photo = create_photo(self.album, "in_album.jpg")
        tag_photo(photo, create_tag("Beach"))
        other = create_album("/2023/", title="Other")
        create_photo(other, "elsewhere.jpg")

        _path, rendered = self.build_capturing_photos(album_id=self.album.id)

        self.assertEqual([p.file for p in rendered], ["in_album.jpg"])

    def test_the_filename_still_comes_from_the_album(self):
        path = self.build(album_id=self.album.id)

        self.assertTrue(path.endswith("Holiday.pdf"))

    def test_an_untitled_album_falls_back_to_its_id(self):
        untitled = create_album("/2022/")

        path = self.build(album_id=untitled.id)

        self.assertTrue(path.endswith(f"{untitled.id}.pdf"))

    def test_an_unknown_album_id_fails_cleanly(self):
        self.assertIsNone(self.build(album_id=9999))

    def test_calling_with_neither_argument_writes_a_none_pdf(self):
        # Neither the album nor tag query runs, so `photos` stays the empty
        # queryset it's initialised to -- not the every-untagged-photo query
        # this used to fall through to.
        create_photo(self.album, "a.jpg")

        path = self.build()

        self.assertTrue(path.endswith("None.pdf"))

    def test_the_cover_is_fetched_with_the_documented_signature(self):
        # The call used to be album.get_cover(album, 700) -- self passed
        # explicitly plus a size -- but Album.get_cover takes no arguments
        # and returns a Photo, not a path. Any album with a cover set used
        # to fail before a single page was written. The command now calls
        # album.get_cover() to get the Photo, then cover_photo.get_thumbnail(700)
        # for the path, same as every other photo.
        create_photo(self.album, "cover.jpg", album_cover=True)

        self.build(album_id=self.album.id)


class OutputPathTests(CreateAlbumTestCase):
    def setUp(self):
        super().setUp()
        self.beach = create_tag("Beach")

    def test_a_missing_albums_directory_is_created(self):
        os.rmdir(os.path.join(self.photo_root, "albums"))

        path = self.build(tag_id=self.beach.id)

        self.assertTrue(os.path.exists(path))

    def test_a_name_containing_a_slash_does_not_escape_the_output_directory(self):
        # The filename is sanitised before being joined into the path, so a
        # tag or album title with a slash can no longer write somewhere
        # unintended.
        slashed = create_tag("Trips/2024")

        path = self.build(tag_id=slashed.id)

        self.assertEqual(os.path.dirname(path), os.path.join(self.photo_root, "albums"))
        self.assertTrue(path.endswith("Trips-2024.pdf"))

    def test_the_output_lands_inside_photo_root(self):
        # Worth noting alongside files_scan_albums, which walks PHOTO_ROOT and
        # will report albums/ as a directory with no Album row unless it is
        # covered by IGNORE_FOLDERS.
        path = self.build(tag_id=self.beach.id)

        self.assertTrue(path.startswith(self.photo_root))
        self.assertIn(os.sep + "albums" + os.sep, path)

    def test_rebuilding_overwrites_the_previous_pdf(self):
        first = self.build(tag_id=self.beach.id)
        first_size = os.path.getsize(first)

        photo = create_photo(create_album("/2024/", title="Holiday"), "a.jpg")
        tag_photo(photo, self.beach)
        second = self.build(tag_id=self.beach.id)

        self.assertEqual(first, second)
        self.assertGreater(os.path.getsize(second), first_size)


class PageContentTests(CreateAlbumTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/", title="Holiday", date_display="Summer 2024")
        self.beach = create_tag("Beach")

    def test_a_photo_title_is_rendered(self):
        photo = create_photo(self.album, "a.jpg", title="On the pier")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        self.assertGreater(os.path.getsize(path), 0)

    def test_an_untitled_photo_still_renders(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        self.assertTrue(os.path.exists(path))

    def test_an_ampersand_in_a_title_is_tolerated(self):
        photo = create_photo(self.album, "a.jpg", title="Fish & Chips")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        self.assertTrue(os.path.exists(path))

    def test_an_unmatched_tag_in_a_title_does_not_break_the_build(self):
        # make_font_tag escapes its text, so anything that looks like markup
        # -- album titles, date_display and tag names all reach the paragraph
        # parser the same way -- renders as literal text instead of aborting.
        photo = create_photo(self.album, "a.jpg", title="<b>Brighton")
        tag_photo(photo, self.beach)

        path = self.build(tag_id=self.beach.id)

        self.assertTrue(os.path.exists(path))

    def test_a_thumbnail_that_cannot_be_opened_is_fatal(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        with (
            patch.object(Photo, "get_thumbnail", create=True, return_value="/missing.jpg"),
            self.assertRaises(OSError),
        ):
            make(tag_id=self.beach.id)

    def test_the_thumbnail_size_requested_is_700(self):
        photo = create_photo(self.album, "a.jpg")
        tag_photo(photo, self.beach)

        with patch.object(Photo, "get_thumbnail", create=True, return_value="/thumb.jpg") as thumb:
            make(tag_id=self.beach.id)

        self.assertEqual(thumb.call_args.args[0], 700)


class AlbumModelAssumptionTests(PhotoRootTestCase):
    """Pins the model API this module depends on, so drift is caught early."""

    def test_photo_exposes_get_thumbnail(self):
        self.assertTrue(
            hasattr(Photo, "get_thumbnail"),
            "create_album calls photo.get_thumbnail(700); if this fails the export "
            "cannot run at all",
        )
