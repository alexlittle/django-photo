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

        tags = []
        for location in locations:
            if location.get_lat() is None or location.get_lat() == "0":
                tags.append(location)

        print(len(tags))
        for tag in tags:
            print("--------------------")
            print(tag.name)
            print(f"Edit: {get_domain()}/admin/photo/tag/{tag.id}/change/")
            print(f"Photos: {get_domain()}/tag/{tag.slug}")
            params = {
                "q": tag.name.encode("utf-8"),
                "username": settings.GEONAMES_USERNAME,
                "maxRows": 20,
            }
            if tag.get_prop("country"):
                params["country"] = tag.get_prop("country")

            url = "https://api.geonames.org/searchJSON?" + urllib.parse.urlencode(params)

            print(url)
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            data_json = json.loads(response.read())

            results = data_json.get("geonames")
            if results is None:
                print(f"GeoNames error: {data_json}")
                continue

            if len(results) > 0:
                for i in range(0, min(20, len(results))):
                    try:
                        top_name = results[i]["toponymName"]
                        name = results[i]["name"]
                        admin_name = results[i]["adminName1"]
                        country_code = results[i]["countryCode"]
                        print(f"{i} : {top_name}, {name}, {admin_name}, {country_code}")
                    except (IndexError, KeyError):
                        pass
                accept = input("Accept this? [0-19/Ignore/No]")

                if accept == "i":
                    print("ignoring")
                elif accept == "n":
                    print("no")
                else:
                    try:
                        idx = int(accept)
                    except ValueError:
                        idx = None

                    if idx is None or not (0 <= idx < len(results)):
                        print("invalid selection, ignoring")
                    else:
                        print("accepted")
                        lat = results[idx]["lat"]
                        lng = results[idx]["lng"]
                        country_code = results[idx]["countryCode"]
                        cc_obj, _ = TagProps.objects.get_or_create(tag=tag, name="country")
                        cc_obj.value = country_code
                        cc_obj.save()
                        lat_obj, _ = TagProps.objects.get_or_create(tag=tag, name="lat")
                        lat_obj.value = lat
                        lat_obj.save()
                        lng_obj, _ = TagProps.objects.get_or_create(tag=tag, name="lng")
                        lng_obj.value = lng
                        lng_obj.save()
