"""Tests for ``photo.export.views``: ``MakeViewPDF`` and ``TagToFolderView``.

``MakeViewPDF`` delegates the actual PDF build to ``photo.export.create_album.make``
(covered in depth by test_create_album.py) so it is patched here -- these tests
only cover the view's own plumbing: 404 handling and the response it builds.
``TagToFolderView`` copies files on disk, so it inherits ``PhotoRootTestCase``.
"""

import os
from unittest.mock import patch

from django.urls import reverse

from tests.base import PhotoRootTestCase, create_album, create_photo, create_tag, tag_photo

MAKE = "photo.export.views.create_album.make"


class MakeViewPDFTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def url(self, album_id):
        return reverse("photo:export_pdf", kwargs={"album_id": album_id})

    def write_pdf(self, name="export-album.pdf"):
        path = os.path.join(self.photo_root, name)
        with open(path, "wb") as handle:
            handle.write(b"%PDF-1.4 fake pdf contents")
        return path

    def test_serves_the_generated_pdf(self):
        path = self.write_pdf()

        with patch(MAKE, return_value=path) as make:
            response = self.client.get(self.url(self.album.id))

        make.assert_called_once_with(self.album.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        content = b"".join(response.streaming_content)
        self.assertEqual(content, b"%PDF-1.4 fake pdf contents")

    def test_content_disposition_names_the_album(self):
        path = self.write_pdf()

        with patch(MAKE, return_value=path):
            response = self.client.get(self.url(self.album.id))

        self.assertEqual(
            response["Content-Disposition"], f"inline; filename=export-album{self.album.id}.pdf"
        )

    def test_unknown_album_returns_404_before_building_anything(self):
        with patch(MAKE) as make:
            response = self.client.get(self.url(9999))

        make.assert_not_called()
        self.assertEqual(response.status_code, 404)

    def test_a_missing_pdf_on_disk_returns_404(self):
        missing_path = os.path.join(self.photo_root, "does-not-exist.pdf")

        with patch(MAKE, return_value=missing_path):
            response = self.client.get(self.url(self.album.id))

        self.assertEqual(response.status_code, 404)


class TagToFolderViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.beach = create_tag("Beach")

    def url(self, slug):
        return reverse("photo:export_tag_to_folder", kwargs={"slug": slug})

    def dest_dir(self, slug):
        return os.path.join(self.photo_root, "export", slug)

    def test_tagged_photos_are_copied_into_a_slug_named_folder(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)

        self.client.post(self.url(self.beach.slug))

        self.assertTrue(os.path.exists(os.path.join(self.dest_dir(self.beach.slug), "a.jpg")))

    def test_untagged_photos_are_left_out(self):
        tagged = create_photo(self.album, "tagged.jpg")
        self.write_image(tagged)
        untagged = create_photo(self.album, "untagged.jpg")
        self.write_image(untagged)
        tag_photo(tagged, self.beach)

        self.client.post(self.url(self.beach.slug))

        dest = self.dest_dir(self.beach.slug)
        self.assertTrue(os.path.exists(os.path.join(dest, "tagged.jpg")))
        self.assertFalse(os.path.exists(os.path.join(dest, "untagged.jpg")))

    def test_photos_from_multiple_albums_are_gathered(self):
        other = create_album("/2023/")
        first = create_photo(self.album, "a.jpg")
        second = create_photo(other, "b.jpg")
        self.write_image(first)
        self.write_image(second)
        tag_photo(first, self.beach)
        tag_photo(second, self.beach)

        self.client.post(self.url(self.beach.slug))

        dest = self.dest_dir(self.beach.slug)
        self.assertTrue(os.path.exists(os.path.join(dest, "a.jpg")))
        self.assertTrue(os.path.exists(os.path.join(dest, "b.jpg")))

    def test_leading_slash_in_the_album_name_is_stripped_from_the_source_path(self):
        # Album names are stored with a leading "/"; naive os.path.join would
        # treat that as absolute and escape PHOTO_ROOT entirely.
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        tag_photo(photo, self.beach)

        response = self.client.post(self.url(self.beach.slug))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(os.path.exists(os.path.join(self.dest_dir(self.beach.slug), "a.jpg")))

    def test_redirects_to_the_tag_page(self):
        response = self.client.post(self.url(self.beach.slug))

        self.assertRedirects(
            response,
            reverse("photo:tag_slug", kwargs={"slug": self.beach.slug}),
            fetch_redirect_response=False,
        )

    def test_a_tag_with_no_photos_still_creates_the_folder(self):
        self.client.post(self.url(self.beach.slug))

        self.assertTrue(os.path.isdir(self.dest_dir(self.beach.slug)))

    def test_unknown_slug_returns_404(self):
        response = self.client.post(self.url("does-not-exist"))

        self.assertEqual(response.status_code, 404)

    def test_a_missing_source_file_raises(self):
        photo = create_photo(self.album, "ghost.jpg")
        tag_photo(photo, self.beach)

        with self.assertRaises(FileNotFoundError):
            self.client.post(self.url(self.beach.slug))
