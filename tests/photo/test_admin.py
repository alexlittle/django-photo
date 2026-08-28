"""Tests for ``photo.admin``.

Admin classes are exercised directly (calling their methods/actions with a
plain queryset and a ``None`` request) rather than through the admin site's
HTTP views -- the logic worth covering lives in the custom list_display
callables and actions, not in Django's own admin machinery.
"""

from unittest.mock import patch

from django.urls import reverse

from photo.admin import AlbumAdmin, PhotoAdmin, TagAdmin
from photo.models import Album, Photo, Tag, TagCategory
from tests.base import PhotoRootTestCase, create_album, create_photo, create_tag


class AlbumAdminTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.admin = AlbumAdmin(model=Album, admin_site=None)

    def test_view_url_links_to_the_album_page(self):
        album = create_album("/2024/")

        html = self.admin.view_url(album)

        self.assertIn(reverse("photo:album", args=(album.id,)), html)
        self.assertIn(">View<", html)

    def test_count_reflects_the_number_of_photos_in_the_album(self):
        album = create_album("/2024/")
        create_photo(album, "a.jpg")
        create_photo(album, "b.jpg")
        create_photo(create_album("/2023/"), "elsewhere.jpg")

        self.assertEqual(self.admin.count(album), 2)

    def test_count_is_zero_for_an_empty_album(self):
        album = create_album("/2024/")

        self.assertEqual(self.admin.count(album), 0)


class PhotoAdminTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.admin = PhotoAdmin(model=Photo, admin_site=None)
        self.album = create_album("/2024/")

    def test_edit_photo_links_to_the_edit_page(self):
        photo = create_photo(self.album, "a.jpg")

        html = self.admin.edit_photo(photo)

        self.assertIn(reverse("photo:edit", args=(photo.id,)), html)
        self.assertIn("target='_blank'", html)

    def test_albumid_returns_the_photos_album_id(self):
        photo = create_photo(self.album, "a.jpg")

        self.assertEqual(self.admin.albumid(photo), self.album.id)

    def test_rename_file_action_renames_every_photo_in_the_queryset(self):
        first = create_photo(self.album, "a.jpg")
        second = create_photo(self.album, "b.jpg")

        with patch("photo.admin.rename_photo_file") as rename:
            self.admin.rename_file(None, Photo.objects.filter(album=self.album))

        renamed = [call.args[0] for call in rename.call_args_list]
        self.assertCountEqual(renamed, [first, second])

    def test_rename_file_action_on_an_empty_queryset_is_a_no_op(self):
        with patch("photo.admin.rename_photo_file") as rename:
            self.admin.rename_file(None, Photo.objects.none())

        rename.assert_not_called()


class TagAdminTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.admin = TagAdmin(model=Tag, admin_site=None)

    def test_view_url_links_to_the_tag_page(self):
        tag = create_tag("Beach")

        html = self.admin.view_url(tag)

        self.assertIn(reverse("photo:tag_slug", args=(tag.slug,)), html)
        self.assertIn(">View<", html)

    def test_mark_category_place_sets_the_place_category_on_every_tag_in_the_queryset(self):
        place = TagCategory.objects.create(name="Place")
        TagCategory.objects.create(name="Person")
        beach = create_tag("Beach")
        hills = create_tag("Hills")
        untouched = create_tag("Grandma")

        self.admin.mark_category_place(None, Tag.objects.filter(id__in=[beach.id, hills.id]))

        beach.refresh_from_db()
        hills.refresh_from_db()
        untouched.refresh_from_db()
        self.assertEqual(beach.tagcategory, place)
        self.assertEqual(hills.tagcategory, place)
        self.assertIsNone(untouched.tagcategory)

    def test_every_mark_category_action_assigns_the_matching_category(self):
        actions_and_names = [
            ("mark_category_place", "Place"),
            ("mark_category_person", "Person"),
            ("mark_category_animal", "Animal"),
            ("mark_category_date", "Date"),
            ("mark_category_object", "Object"),
            ("mark_category_food", "Food"),
            ("mark_category_event", "Event"),
            ("mark_category_activity", "Activity"),
            ("mark_category_organisation", "Organisation"),
            ("mark_category_label", "Label"),
        ]
        for action_name, category_name in actions_and_names:
            category = TagCategory.objects.create(name=category_name)
            tag = create_tag(f"tag-for-{category_name}")

            getattr(self.admin, action_name)(None, Tag.objects.filter(id=tag.id))

            tag.refresh_from_db()
            self.assertEqual(
                tag.tagcategory, category, f"{action_name} did not assign {category_name}"
            )

    def test_mark_category_action_raises_when_the_category_does_not_exist(self):
        tag = create_tag("Beach")

        with self.assertRaises(TagCategory.DoesNotExist):
            self.admin.mark_category_place(None, Tag.objects.filter(id=tag.id))
