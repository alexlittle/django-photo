"""
Management command to get lat/lng for places
"""

import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.lib import get_domain
from photo.models import Tag, TagProps


class Command(BaseCommand):
    help = "gets lat/lng for locations"

    def handle(self, *args, **options):
        locations = Tag.objects.filter(tagcategory__name="Location")
        tags = [location for location in locations if self.needs_coordinates(location)]

        print(len(tags))
        for tag in tags:
            self.geocode_tag(tag)

    def needs_coordinates(self, tag):
        lat = tag.get_lat()
        return lat is None or lat == "0"

    def build_search_url(self, tag):
        params = {
            "q": tag.name.encode("utf-8"),
            "username": settings.GEONAMES_USERNAME,
            "maxRows": 20,
        }
        country = tag.get_prop("country")
        if country:
            params["country"] = country
        return "https://api.geonames.org/searchJSON?" + urllib.parse.urlencode(params)

    def fetch_results(self, url):
        print(url)
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    def print_candidates(self, results):
        for i in range(0, min(20, len(results))):
            try:
                top_name = results[i]["toponymName"]
                name = results[i]["name"]
                admin_name = results[i]["adminName1"]
                country_code = results[i]["countryCode"]
                print(f"{i} : {top_name}, {name}, {admin_name}, {country_code}")
            except (IndexError, KeyError):
                pass

    def parse_selection(self, accept, num_results):
        try:
            idx = int(accept)
        except ValueError:
            return None
        return idx if 0 <= idx < num_results else None

    def apply_selection(self, tag, result):
        cc_obj, _ = TagProps.objects.get_or_create(tag=tag, name="country")
        cc_obj.value = result["countryCode"]
        cc_obj.save()

        lat_obj, _ = TagProps.objects.get_or_create(tag=tag, name="lat")
        lat_obj.value = result["lat"]
        lat_obj.save()

        lng_obj, _ = TagProps.objects.get_or_create(tag=tag, name="lng")
        lng_obj.value = result["lng"]
        lng_obj.save()

    def geocode_tag(self, tag):
        print("--------------------")
        print(tag.name)
        print(f"Edit: {get_domain()}/admin/photo/tag/{tag.id}/change/")
        print(f"Photos: {get_domain()}/tag/{tag.slug}")

        data_json = self.fetch_results(self.build_search_url(tag))
        results = data_json.get("geonames")
        if results is None:
            print(f"GeoNames error: {data_json}")
            return

        if not results:
            return

        self.print_candidates(results)
        accept = input("Accept this? [0-19/Ignore/No]")

        if accept == "i":
            print("ignoring")
            return
        if accept == "n":
            print("no")
            return

        idx = self.parse_selection(accept, len(results))
        if idx is None:
            print("invalid selection, ignoring")
            return

        print("accepted")
        self.apply_selection(tag, results[idx])
