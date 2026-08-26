"""Tests for the read-only browsing views.

HomeView, AlbumView, TagSlugView, CloudView, CloudCategoryView, MapView,
SearchView and PhotoFavouritesView.
"""

from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from photo.models import TagCategory
from tests.base import (
    create_album,
    create_photo,
    create_tag,
    make_datetime,
    set_photo_prop,
    set_tag_prop,
    tag_photo,
)


class HomeViewTests(TestCase):
    def test_renders(self):
        response = self.client.get(reverse("photo:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/home.html")

    def test_albums_ordered_by_most_recent_photo(self):
        old = create_album("/2022/")
        new = create_album("/2024/")
        empty = create_album("/empty/")
        create_photo(old, "old.jpg", make_datetime(2022, 6, 1))
        create_photo(new, "new.jpg", make_datetime(2024, 6, 1))

        albums = list(self.client.get(reverse("photo:home")).context["albums"])

        self.assertLess(albums.index(new), albums.index(old))
        self.assertIn(empty, albums, "albums with no photos should still be listed")

    def test_years_context_only_contains_date_tags(self):
        date_category = TagCategory.objects.create(name="Date")
        people_category = TagCategory.objects.create(name="People")
        year = create_tag("2024", date_category)
        create_tag("Alice", people_category)
        create_tag("Uncategorised")

        response = self.client.get(reverse("photo:home"))

        self.assertEqual(list(response.context["years"]), [year])

    def test_pagination(self):
        # paginate_by is read from settings at import time, so override_settings
        # will not change it -- build the fixture from the live value instead.
        per_page = settings.ALBUMS_PER_PAGE
        for index in range(per_page + 1):
            create_album(f"/album-{index}/")

        response = self.client.get(reverse("photo:home"))

        self.assertEqual(len(response.context["albums"]), per_page)
        self.assertTrue(response.context["page_obj"].has_next())


class AlbumViewTests(TestCase):
    def setUp(self):
        self.album = create_album("/2024/")
        self.url = reverse("photo:album", kwargs={"album_id": self.album.id})

    def test_unknown_album_returns_404(self):
        response = self.client.get(reverse("photo:album", kwargs={"album_id": 9999}))

        self.assertEqual(response.status_code, 404)

    def test_lists_only_photos_in_this_album_ordered_by_date(self):
        second = create_photo(self.album, "b.jpg", make_datetime(2024, 3, 1))
        first = create_photo(self.album, "a.jpg", make_datetime(2024, 1, 1))
        other_album = create_album("/2023/")
        elsewhere = create_photo(other_album, "c.jpg", make_datetime(2023, 1, 1))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/album.html")
        self.assertEqual(list(response.context["photos"]), [first, second])
        self.assertNotIn(elsewhere, response.context["photos"])
        self.assertEqual(response.context["album"], self.album)
        self.assertEqual(response.context["photo_count"], 2)

    def test_photos_with_the_same_date_fall_back_to_filename_order(self):
        same_date = make_datetime(2024, 1, 1)
        beta = create_photo(self.album, "b.jpg", same_date)
        alpha = create_photo(self.album, "a.jpg", same_date)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["photos"]), [alpha, beta])

    def test_print_view_excludes_photos_flagged_for_export(self):
        keep = create_photo(self.album, "keep.jpg")
        drop = create_photo(self.album, "drop.jpg")
        set_photo_prop(drop, "exclude.album.export", "true")

        response = self.client.get(self.url, {"view": "print"})

        self.assertEqual(list(response.context["photos"]), [keep])
        self.assertEqual(response.context["photo_count"], 1)

    def test_print_view_keeps_photos_where_the_flag_is_not_true(self):
        photo = create_photo(self.album, "keep.jpg")
        set_photo_prop(photo, "exclude.album.export", "false")

        response = self.client.get(self.url, {"view": "print"})

        self.assertEqual(list(response.context["photos"]), [photo])

    def test_checked_photo_ids_are_echoed_back(self):
        response = self.client.get(self.url, {"photo_id": ["1", "2"]})

        self.assertEqual(response.context["photos_checked"], ["1", "2"])

    def test_photos_checked_defaults_to_empty(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context["photos_checked"], [])


class TagSlugViewTests(TestCase):
    def setUp(self):
        self.album = create_album("/2024/")
        self.beach = create_tag("Beach")
        self.sunset = create_tag("Sunset")

    def url(self, slug):
        return reverse("photo:tag_slug", kwargs={"slug": slug})

    def test_single_tag_returns_matching_photos(self):
        tagged = create_photo(self.album, "a.jpg")
        untagged = create_photo(self.album, "b.jpg")
        tag_photo(tagged, self.beach)

        response = self.client.get(self.url("beach"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/tag.html")
        self.assertEqual(list(response.context["photos"]), [tagged])
        self.assertNotIn(untagged, response.context["photos"])
        self.assertEqual(list(response.context["tags"]), [self.beach])

    def test_multiple_slugs_require_all_tags(self):
        both = create_photo(self.album, "both.jpg", make_datetime(2024, 1, 1))
        only_beach = create_photo(self.album, "one.jpg", make_datetime(2024, 2, 1))
        tag_photo(both, self.beach, self.sunset)
        tag_photo(only_beach, self.beach)

        response = self.client.get(self.url("beach+sunset"))

        self.assertEqual(list(response.context["photos"]), [both])

    def test_multiple_slugs_puts_both_tags_in_context(self):
        response = self.client.get(self.url("beach+sunset"))

        self.assertCountEqual(response.context["tags"], [self.beach, self.sunset])

    def test_unknown_slug_returns_empty_list_not_404(self):
        response = self.client.get(self.url("nope"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["photos"]), [])

    def test_results_ordered_by_date(self):
        later = create_photo(self.album, "later.jpg", make_datetime(2024, 6, 1))
        earlier = create_photo(self.album, "earlier.jpg", make_datetime(2024, 1, 1))
        tag_photo(later, self.beach)
        tag_photo(earlier, self.beach)

        response = self.client.get(self.url("beach"))

        self.assertEqual(list(response.context["photos"]), [earlier, later])


class CloudViewTests(TestCase):
    def test_lists_all_tags_and_categories(self):
        category = TagCategory.objects.create(name="People")
        alice = create_tag("Alice", category)
        bob = create_tag("Bob")

        response = self.client.get(reverse("photo:cloud"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/cloud.html")
        self.assertCountEqual(response.context["tags"], [alice, bob])
        self.assertEqual(list(response.context["categories"]), [category])


class CloudCategoryViewTests(TestCase):
    def test_filters_tags_by_category_name(self):
        people = TagCategory.objects.create(name="People")
        places = TagCategory.objects.create(name="Location")
        alice = create_tag("Alice", people)
        create_tag("Harrogate", places)

        response = self.client.get(reverse("photo:cloud_category", kwargs={"category": "People"}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/cloud_category.html")
        self.assertEqual([tag["name"] for tag in response.context["tags"]], [alice.name])

    def test_annotates_photo_count(self):
        people = TagCategory.objects.create(name="People")
        alice = create_tag("Alice", people)
        album = create_album("/2024/")
        tag_photo(create_photo(album, "a.jpg"), alice)
        tag_photo(create_photo(album, "b.jpg"), alice)

        response = self.client.get(reverse("photo:cloud_category", kwargs={"category": "People"}))

        self.assertEqual(response.context["tags"][0]["count"], 2)

    def test_unknown_category_is_empty(self):
        response = self.client.get(reverse("photo:cloud_category", kwargs={"category": "Nope"}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["tags"]), [])


class MapViewTests(TestCase):
    def setUp(self):
        self.location = TagCategory.objects.create(name="Location")

        self.harrogate = create_tag("Harrogate", self.location)
        set_tag_prop(self.harrogate, "source", "me")
        set_tag_prop(self.harrogate, "lat", "53.99")
        set_tag_prop(self.harrogate, "lng", "-1.54")

        self.unlocated = create_tag("Unlocated", self.location)
        set_tag_prop(self.unlocated, "source", "me")
        set_tag_prop(self.unlocated, "lat", "0")

        self.hidden = create_tag("Hidden", self.location)
        set_tag_prop(self.hidden, "source", "me")
        set_tag_prop(self.hidden, "lat", "54.0")
        set_tag_prop(self.hidden, "map.display", "false")

        self.paris = create_tag("Paris", self.location)
        set_tag_prop(self.paris, "source", "osm")
        set_tag_prop(self.paris, "lat", "48.85")

        people = TagCategory.objects.create(name="People")
        self.alice = create_tag("Alice", people)
        set_tag_prop(self.alice, "source", "me")

    def test_defaults_to_the_me_source(self):
        response = self.client.get(reverse("photo:map"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/map.html")
        self.assertEqual(list(response.context["tags"]), [self.harrogate])

    def test_excludes_zero_latitude_hidden_and_other_categories(self):
        tags = list(self.client.get(reverse("photo:map")).context["tags"])

        self.assertNotIn(self.unlocated, tags)
        self.assertNotIn(self.hidden, tags)
        self.assertNotIn(self.alice, tags)

    def test_source_can_be_overridden(self):
        response = self.client.get(reverse("photo:map"), {"source": "osm"})

        self.assertEqual(list(response.context["tags"]), [self.paris])

    def test_sources_list_only_covers_location_tags(self):
        response = self.client.get(reverse("photo:map"))

        self.assertCountEqual(response.context["sources"], ["me", "osm"])

    def test_unknown_source_returns_nothing(self):
        response = self.client.get(reverse("photo:map"), {"source": "nope"})

        self.assertEqual(list(response.context["tags"]), [])


# CombinedSearchManager.combined_search runs MySQL-specific raw SQL (MATCH ...
# AGAINST), so it is patched out here. That keeps these tests about the view's
# behaviour and lets them run on any backend.
@patch("photo.models.CombinedSearchManager.combined_search")
class SearchViewTests(TestCase):
    def setUp(self):
        self.album = create_album("/2024/")
        self.url = reverse("photo:search")

    def test_blank_query_skips_the_search_entirely(self, combined_search):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/search.html")
        self.assertEqual(list(response.context["results"]), [])
        self.assertEqual(response.context["total_results"], 0)
        combined_search.assert_not_called()

    def test_whitespace_only_query_is_treated_as_blank(self, combined_search):
        response = self.client.get(self.url, {"q": "   "})

        self.assertEqual(response.context["query"], "")
        combined_search.assert_not_called()

    def test_returns_photos_for_the_ids_the_search_reports(self, combined_search):
        match = create_photo(self.album, "match.jpg")
        create_photo(self.album, "other.jpg")
        combined_search.return_value = [{"id": match.id}]

        response = self.client.get(self.url, {"q": "beach"})

        self.assertEqual(list(response.context["results"]), [match])
        self.assertEqual(response.context["total_results"], 1)
        self.assertEqual(response.context["query"], "beach")
        combined_search.assert_any_call("beach")

    def test_query_is_stripped_before_searching(self, combined_search):
        combined_search.return_value = []

        self.client.get(self.url, {"q": "  beach  "})

        combined_search.assert_any_call("beach")

    def test_search_form_is_prefilled(self, combined_search):
        combined_search.return_value = []

        response = self.client.get(self.url, {"q": "beach"})

        self.assertEqual(response.context["form"].initial["q"], "beach")

    def test_ids_that_no_longer_exist_are_ignored(self, combined_search):
        combined_search.return_value = [{"id": 9999}]

        response = self.client.get(self.url, {"q": "beach"})

        self.assertEqual(list(response.context["results"]), [])


class PhotoFavouritesViewTests(TestCase):
    def setUp(self):
        self.album = create_album("/2024/")
        self.url = reverse("photo:favourites")

    def test_lists_only_favourites_newest_first(self):
        older = create_photo(self.album, "older.jpg", make_datetime(2024, 1, 1))
        newer = create_photo(self.album, "newer.jpg", make_datetime(2024, 6, 1))
        not_favourite = create_photo(self.album, "plain.jpg")
        set_photo_prop(older, "favourite", "true")
        set_photo_prop(newer, "favourite", "true")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "photo/favourites.html")
        self.assertEqual(list(response.context["photos"]), [newer, older])
        self.assertNotIn(not_favourite, response.context["photos"])

    def test_unstarred_photos_are_excluded(self):
        photo = create_photo(self.album, "a.jpg")
        set_photo_prop(photo, "favourite", "false")

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["photos"]), [])
