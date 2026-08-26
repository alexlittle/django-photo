"""Tests for the image-serving and single-photo action views.

PhotoView, PhotoViewAnnotated, PhotoSetCoverView, PhotoStarView,
PhotoUnstarView and AlbumExifUpdateView.
"""

import io
import json
import os
from unittest.mock import patch

from django.urls import reverse
from PIL import Image

from photo.models import Photo, PhotoProps
from tests.base import (
    PhotoRootTestCase,
    create_album,
    create_photo,
    set_photo_prop,
)


class PhotoViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def url(self, photo_id):
        return reverse("photo:view", kwargs={"photo_id": photo_id})

    def test_serves_the_image_as_jpeg(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo, size=(40, 30))

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        served = Image.open(io.BytesIO(response.content))
        self.assertEqual(served.format, "JPEG")
        self.assertEqual(served.size, (40, 30))

    def test_falls_back_to_png_when_the_mode_cannot_be_written_as_jpeg(self):
        photo = create_photo(self.album, "a.png")
        self.write_image(photo, mode="RGBA", image_format="PNG")

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(Image.open(io.BytesIO(response.content)).format, "PNG")

    def test_missing_file_on_disk_returns_404(self):
        photo = create_photo(self.album, "gone.jpg")

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 404)

    def test_unknown_photo_returns_404(self):
        response = self.client.get(self.url(9999))

        self.assertEqual(response.status_code, 404)

    def test_leading_slash_in_the_album_name_is_stripped_from_the_path(self):
        # Album names are stored as "/2024/"; naive os.path.join would treat
        # that as absolute and escape PHOTO_ROOT entirely.
        photo = create_photo(create_album("/nested/"), "a.jpg")
        self.write_image(photo)

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)


class PhotoViewAnnotatedTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def url(self, photo_id):
        return reverse("photo:view_annotated", kwargs={"photo_id": photo_id})

    def test_draws_boxes_and_serves_jpeg(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo, size=(60, 60))
        set_photo_prop(photo, "face_annotate", json.dumps([[5, 5, 40, 40]]))

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        annotated = Image.open(io.BytesIO(response.content))
        self.assertEqual(annotated.size, (60, 60))

    def test_handles_multiple_boxes(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo, size=(80, 80))
        set_photo_prop(photo, "face_annotate", json.dumps([[5, 5, 30, 30], [40, 40, 70, 70]]))

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)

    def test_empty_box_list_still_serves_the_image(self):
        photo = create_photo(self.album, "a.jpg")
        self.write_image(photo)
        set_photo_prop(photo, "face_annotate", "[]")

        response = self.client.get(self.url(photo.id))

        self.assertEqual(response.status_code, 200)

    def test_unknown_photo_returns_404(self):
        response = self.client.get(self.url(9999))

        self.assertEqual(response.status_code, 404)


class PhotoSetCoverViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_sets_the_cover_and_redirects_to_the_album(self):
        photo = create_photo(self.album, "a.jpg")

        response = self.client.get(reverse("photo:set_cover", kwargs={"photo_id": photo.id}))

        photo.refresh_from_db()
        self.assertTrue(photo.album_cover)
        self.assertRedirects(
            response,
            reverse("photo:album", kwargs={"album_id": self.album.id}),
            fetch_redirect_response=False,
        )

    def test_previous_cover_in_the_same_album_is_cleared(self):
        old_cover = create_photo(self.album, "old.jpg", album_cover=True)
        new_cover = create_photo(self.album, "new.jpg")

        self.client.get(reverse("photo:set_cover", kwargs={"photo_id": new_cover.id}))

        old_cover.refresh_from_db()
        new_cover.refresh_from_db()
        self.assertFalse(old_cover.album_cover)
        self.assertTrue(new_cover.album_cover)

    def test_covers_in_other_albums_are_untouched(self):
        other_album = create_album("/2023/")
        other_cover = create_photo(other_album, "other.jpg", album_cover=True)
        photo = create_photo(self.album, "a.jpg")

        self.client.get(reverse("photo:set_cover", kwargs={"photo_id": photo.id}))

        other_cover.refresh_from_db()
        self.assertTrue(other_cover.album_cover)

    def test_unknown_photo_returns_404(self):
        response = self.client.get(reverse("photo:set_cover", kwargs={"photo_id": 9999}))

        self.assertEqual(response.status_code, 404)


class PhotoStarViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.photo = create_photo(self.album, "a.jpg")

    def test_star_sets_the_favourite_prop_and_redirects(self):
        response = self.client.get(reverse("photo:star", kwargs={"photo_id": self.photo.id}))

        self.assertEqual(self.photo.get_prop("favourite"), "true")
        self.assertRedirects(
            response,
            reverse("photo:album", kwargs={"album_id": self.album.id}),
            fetch_redirect_response=False,
        )

    def test_unstar_sets_the_favourite_prop_to_false(self):
        self.client.get(reverse("photo:unstar", kwargs={"photo_id": self.photo.id}))

        self.assertEqual(self.photo.get_prop("favourite"), "false")

    def test_starring_twice_updates_rather_than_duplicates(self):
        url = reverse("photo:star", kwargs={"photo_id": self.photo.id})

        self.client.get(url)
        self.client.get(url)

        props = PhotoProps.objects.filter(photo=self.photo, name="favourite")
        self.assertEqual(props.count(), 1)

    def test_star_then_unstar_leaves_a_single_prop(self):
        self.client.get(reverse("photo:star", kwargs={"photo_id": self.photo.id}))
        self.client.get(reverse("photo:unstar", kwargs={"photo_id": self.photo.id}))

        self.assertEqual(PhotoProps.objects.filter(photo=self.photo).count(), 1)
        self.assertEqual(self.photo.get_prop("favourite"), "false")

    def test_unknown_photo_returns_404(self):
        self.assertEqual(
            self.client.get(reverse("photo:star", kwargs={"photo_id": 9999})).status_code, 404
        )
        self.assertEqual(
            self.client.get(reverse("photo:unstar", kwargs={"photo_id": 9999})).status_code, 404
        )


class AlbumExifUpdateViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")

    def test_writes_metadata_for_every_photo_in_the_album(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")
        elsewhere = create_photo(create_album("/2023/"), "c.jpg")

        with patch("photo.views.add_or_update_xmp_metadata") as write_xmp:
            response = self.client.get(
                reverse("photo:album_exif", kwargs={"album_id": self.album.id})
            )

        updated = [call.args[0] for call in write_xmp.call_args_list]
        self.assertCountEqual(updated, [first, second])
        self.assertNotIn(elsewhere, updated)
        self.assertRedirects(
            response,
            reverse("photo:album", kwargs={"album_id": self.album.id}),
            fetch_redirect_response=False,
        )

    def test_empty_album_is_a_no_op(self):
        with patch("photo.views.add_or_update_xmp_metadata") as write_xmp:
            response = self.client.get(
                reverse("photo:album_exif", kwargs={"album_id": self.album.id})
            )

        write_xmp.assert_not_called()
        self.assertEqual(response.status_code, 302)

    def test_unknown_album_returns_404(self):
        with patch("photo.views.add_or_update_xmp_metadata"):
            response = self.client.get(reverse("photo:album_exif", kwargs={"album_id": 9999}))

        self.assertEqual(response.status_code, 404)


class PhotoDeleteSignalTests(PhotoRootTestCase):
    """The post_delete receiver removes the underlying file."""

    def test_file_is_removed_when_the_photo_is_deleted(self):
        photo = create_photo(create_album("/2024/"), "a.jpg")
        path = self.write_image(photo)

        photo.delete()

        self.assertFalse(Photo.objects.filter(file="a.jpg").exists())
        # Note: the receiver builds its path by string concatenation
        # (PHOTO_ROOT + album.name + file) rather than os.path.join, so it only
        # lines up when PHOTO_ROOT has no trailing slash and album names keep
        # their leading one. Worth tightening -- see the notes with these tests.
        self.assertFalse(os.path.exists(path))

    def test_a_missing_file_does_not_break_the_delete(self):
        photo = create_photo(create_album("/2024/"), "gone.jpg")

        photo.delete()

        self.assertFalse(Photo.objects.filter(file="gone.jpg").exists())
