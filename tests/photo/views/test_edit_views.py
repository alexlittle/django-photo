"""Tests for the views that change data.

ScanFolderView, PhotoEditView and PhotoUpdateTagsView.

``add_tags`` and ``add_or_update_xmp_metadata`` shell out to image metadata
tooling, so they are patched at ``photo.views`` (where they are bound) rather
than at ``photo.lib``.
"""

import os
from datetime import date
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from photo.models import Photo, PhotoTag, Tag
from tests.base import (
    PhotoRootTestCase,
    create_album,
    create_photo,
    create_tag,
    local,
    make_datetime,
    tag_photo,
)


class ScanFolderViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("photo:scan")

    def test_get_renders_with_sensible_defaults(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/scan.html")
        initial = response.context["form"].initial
        self.assertEqual(initial["directory"], f"/{timezone.now().year}/")
        self.assertEqual(initial["default_tags"], "")
        self.assertIsNotNone(initial["default_date"])

    def test_rejects_a_directory_that_does_not_exist(self):
        response = self.client.post(
            self.url,
            {"directory": "/nope/", "default_date": "2024-06-01", "default_tags": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], None, "Directory does not exist")

    def test_directory_is_required(self):
        response = self.client.post(self.url, {"default_date": "2024-06-01"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("directory", response.context["form"].errors)

    def test_valid_scan_runs_the_command_and_redirects_to_the_new_album(self):
        os.makedirs(os.path.join(self.photo_root, "2024"))
        album = create_album("/2024/")

        def fake_command(_name, **kwargs):
            kwargs["stdout"].write(str(album.id))

        target = "photo.views.management.call_command"
        with patch(target, side_effect=fake_command) as call_command:
            response = self.client.post(
                self.url,
                {
                    "directory": "/2024/",
                    "default_date": "2024-06-01",
                    "default_tags": "holiday, beach",
                },
            )

        self.assertRedirects(
            response,
            reverse("photo:album", kwargs={"album_id": album.id}),
            fetch_redirect_response=False,
        )
        self.assertEqual(call_command.call_args.args[0], "upload_album")
        self.assertEqual(call_command.call_args.kwargs["directory"], "/2024/")
        self.assertEqual(call_command.call_args.kwargs["defaulttags"], "holiday, beach")
        self.assertEqual(call_command.call_args.kwargs["defaultdate"], date(2024, 6, 1))

    def test_missing_trailing_slash_is_added_before_the_command_runs(self):
        os.makedirs(os.path.join(self.photo_root, "2024"))
        album = create_album("/2024/")

        def fake_command(_name, **kwargs):
            kwargs["stdout"].write(str(album.id))

        target = "photo.views.management.call_command"
        with patch(target, side_effect=fake_command) as call_command:
            self.client.post(
                self.url,
                {"directory": "/2024", "default_date": "2024-06-01", "default_tags": ""},
            )

        self.assertEqual(call_command.call_args.kwargs["directory"], "/2024/")


class PhotoEditViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.photo = create_photo(
            self.album, "a.jpg", make_datetime(2024, 1, 1, 15, 45), title="Original"
        )
        self.url = reverse("photo:edit", kwargs={"photo_id": self.photo.id})

    def test_get_prefills_the_form(self):
        tag_photo(self.photo, create_tag("Beach"), create_tag("Sunset"))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/edit.html")
        initial = response.context["form"].initial
        self.assertEqual(initial["title"], "Original")
        self.assertCountEqual(initial["tags"].split(", "), ["Beach", "Sunset"])

    def test_get_on_an_unknown_photo_returns_404(self):
        response = self.client.get(reverse("photo:edit", kwargs={"photo_id": 9999}))

        self.assertEqual(response.status_code, 404)

    def test_post_updates_title_and_replaces_tags(self):
        tag_photo(self.photo, create_tag("Old"))

        with (
            patch("photo.views.add_tags") as add_tags,
            patch("photo.views.add_or_update_xmp_metadata") as write_xmp,
        ):
            response = self.client.post(
                self.url,
                {"title": "New title", "tags": "beach, sunset", "date": "2024-03-09"},
            )

        self.photo.refresh_from_db()
        self.assertEqual(self.photo.title, "New title")
        # The view clears the existing rows then delegates to add_tags, which
        # is mocked here -- so nothing should be left behind.
        self.assertEqual(PhotoTag.objects.filter(photo=self.photo).count(), 0)
        add_tags.assert_called_once()
        self.assertEqual(add_tags.call_args.args[0], self.photo)
        self.assertEqual(add_tags.call_args.args[1], "beach, sunset")
        write_xmp.assert_called_once()
        self.assertRedirects(
            response,
            reverse("photo:album", kwargs={"album_id": self.album.id}),
            fetch_redirect_response=False,
        )

    def test_post_keeps_the_original_time_of_day(self):
        with (
            patch("photo.views.add_tags"),
            patch("photo.views.add_or_update_xmp_metadata"),
        ):
            self.client.post(self.url, {"title": "", "tags": "beach", "date": "2024-03-09"})

        self.photo.refresh_from_db()
        updated = local(self.photo.date)
        self.assertEqual(
            (updated.year, updated.month, updated.day, updated.hour, updated.minute),
            (2024, 3, 9, 15, 45),
        )

    def test_tags_are_required(self):
        with (
            patch("photo.views.add_tags") as add_tags,
            patch("photo.views.add_or_update_xmp_metadata"),
        ):
            response = self.client.post(self.url, {"title": "New title", "date": "2024-03-09"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("tags", response.context["form"].errors)
        add_tags.assert_not_called()
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.title, "Original")

    def test_an_invalid_date_leaves_the_photo_alone(self):
        with (
            patch("photo.views.add_tags"),
            patch("photo.views.add_or_update_xmp_metadata"),
        ):
            response = self.client.post(
                self.url, {"title": "New", "tags": "beach", "date": "not-a-date"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("date", response.context["form"].errors)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.title, "Original")


class PhotoUpdateTagsViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = create_album("/2024/")
        self.other_album = create_album("/2023/")
        self.first = create_photo(self.album, "a.jpg", make_datetime(2024, 1, 1))
        self.second = create_photo(self.album, "b.jpg", make_datetime(2024, 2, 1))
        self.next_url = reverse("photo:album", kwargs={"album_id": self.album.id})

    def url(self, *photos):
        # Note: the view reads photo_id from request.GET even on POST, so the
        # ids have to travel in the query string.
        params = "&".join(f"photo_id={photo.id}" for photo in photos)
        return f"{reverse('photo:update_tags')}?{params}"

    def post(self, photos, **data):
        payload = {
            "action": "add",
            "tags": "",
            "album": str(self.album.id),
            "next": self.next_url,
        }
        payload.update(data)
        with patch("photo.views.add_or_update_xmp_metadata") as write_xmp:
            response = self.client.post(self.url(*photos), payload)
        return response, write_xmp

    def test_get_renders_with_next_prefilled(self):
        response = self.client.get(reverse("photo:update_tags"), {"next": self.next_url})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/update_tags.html")
        self.assertEqual(response.context["form"].initial["next"], self.next_url)

    def test_next_defaults_to_root(self):
        response = self.client.get(reverse("photo:update_tags"))

        self.assertEqual(response.context["form"].initial["next"], "/")

    def test_add_applies_tags_to_every_selected_photo(self):
        _response, write_xmp = self.post(
            [self.first, self.second], action="add", tags="beach, sunset"
        )

        for photo in (self.first, self.second):
            applied = Tag.objects.filter(phototag__photo=photo).values_list("name", flat=True)
            self.assertCountEqual(applied, ["beach", "sunset"])
        self.assertTrue(write_xmp.called)

    def test_add_creates_missing_tags_with_a_slug(self):
        self.post([self.first], action="add", tags="Sea View")

        tag = Tag.objects.get(name="Sea View")
        self.assertEqual(tag.slug, "sea-view")

    def test_add_is_idempotent(self):
        beach = create_tag("beach")
        tag_photo(self.first, beach)

        self.post([self.first], action="add", tags="beach")

        self.assertEqual(PhotoTag.objects.filter(photo=self.first, tag=beach).count(), 1)

    def test_add_leaves_unselected_photos_alone(self):
        self.post([self.first], action="add", tags="beach")

        self.assertFalse(PhotoTag.objects.filter(photo=self.second).exists())

    def test_delete_removes_only_the_named_tags(self):
        beach = create_tag("beach")
        sunset = create_tag("sunset")
        tag_photo(self.first, beach, sunset)

        self.post([self.first], action="delete", tags="beach")

        remaining = Tag.objects.filter(phototag__photo=self.first).values_list("name", flat=True)
        self.assertEqual(list(remaining), ["sunset"])

    def test_change_date_updates_every_selected_photo(self):
        self.post([self.first, self.second], action="change_date", date="2024-05-01", tags="")

        for photo in (self.first, self.second):
            photo.refresh_from_db()
            self.assertEqual(local(photo.date).date(), date(2024, 5, 1))

    def test_change_album_moves_the_record_and_the_file(self):
        old_path = self.write_image(self.first)
        self.album_dir(self.other_album)

        self.post([self.first], action="change_album", album=str(self.other_album.id), tags="")

        self.first.refresh_from_db()
        self.assertEqual(self.first.album, self.other_album)
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(os.path.join(self.photo_root, "2023", self.first.file)))

    def test_change_album_skips_photos_whose_file_is_missing(self):
        self.album_dir(self.other_album)

        self.post([self.first], action="change_album", album=str(self.other_album.id), tags="")

        self.first.refresh_from_db()
        self.assertEqual(
            self.first.album,
            self.album,
            "the rename fails, so the album should not have changed either",
        )

    def test_redirect_carries_the_selected_photo_ids(self):
        response, _write_xmp = self.post([self.first, self.second], action="add", tags="beach")

        self.assertEqual(response.status_code, 302)
        location = response["Location"]
        self.assertTrue(location.startswith(self.next_url))
        self.assertIn(f"photo_id={self.first.id}", location)
        self.assertIn(f"photo_id={self.second.id}", location)

    def test_a_next_url_that_already_has_a_query_string_is_not_given_another(self):
        next_with_query = f"{self.next_url}?view=print"
        response, _write_xmp = self.post(
            [self.first], action="add", tags="beach", next=next_with_query
        )

        self.assertEqual(response["Location"].count("?"), 1)

    def test_ids_that_no_longer_exist_are_skipped(self):
        ghost = create_photo(self.album, "ghost.jpg")
        url = f"{reverse('photo:update_tags')}?photo_id={self.first.id}&photo_id={ghost.id}"
        Photo.objects.filter(pk=ghost.pk).delete()

        with patch("photo.views.add_or_update_xmp_metadata"):
            response = self.client.post(
                url,
                {
                    "action": "add",
                    "tags": "beach",
                    "album": str(self.album.id),
                    "next": self.next_url,
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(PhotoTag.objects.filter(photo=self.first).exists())

    def test_next_is_required(self):
        with patch("photo.views.add_or_update_xmp_metadata"):
            response = self.client.post(
                self.url(self.first),
                {"action": "add", "tags": "beach", "album": str(self.album.id)},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("next", response.context["form"].errors)

    def test_an_unknown_action_is_rejected(self):
        with patch("photo.views.add_or_update_xmp_metadata"):
            response = self.client.post(
                self.url(self.first),
                {
                    "action": "explode",
                    "tags": "beach",
                    "album": str(self.album.id),
                    "next": self.next_url,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("action", response.context["form"].errors)
        self.assertFalse(PhotoTag.objects.filter(photo=self.first).exists())
