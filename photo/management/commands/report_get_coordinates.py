
"""
Management command to get lat/lng for places
"""
import urllib
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Tag, TagProps


class Command(BaseCommand):
    help = "gets lat/lng for locations"

    def handle(self, *args, **options):
        locations = Tag.objects.filter(tagcategory__name='Location')

        tags = []
        for location in locations:
            if location.get_lat() is None or location.get_lat() == "0":
                tags.append(location)

        print(len(tags))
        for tag in tags:
            print("--------------------")
            print(tag.name)
            print("Edit: %s/admin/photo/tag/%d/change/" % (settings.DOMAIN_NAME, tag.id))
            print("Photos: %s/tag/%s" % (settings.DOMAIN_NAME, tag.slug))
            params = {
                'q': tag.name.encode('utf-8'),
                'username': settings.GEONAMES_USERNAME,
                'maxRows': 20}
            if tag.get_prop('country'):
                params['country'] = tag.get_prop('country')

            url = 'http://api.geonames.org/searchJSON?' + urllib.parse.urlencode(params)

            print(url)
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            data_json = json.loads(response.read())

            if len(data_json['geonames']) > 0:
                for i in range(0, 20):
                    try:
                        print("%d : %s, %s, %s, %s" % (i, data_json['geonames'][i]['toponymName'],
                                                       data_json['geonames'][i]['name'],
                                                       data_json['geonames'][i]['adminName1'],
                                                       data_json['geonames'][i]['countryCode']))
                    except (IndexError, KeyError):
                        pass
                accept = input("Accept this? [0-19/Ignore/No]")

                if accept == 'i':
                    print('ignoring')
                elif accept == 'n':
                    print('no')
                else:
                    idx = int(accept)
                    print('accepted')
                    lat = data_json['geonames'][idx]['lat']
                    lng = data_json['geonames'][idx]['lng']
                    country_code = data_json['geonames'][idx]['countryCode']
                    cc_obj, created = TagProps.objects.get_or_create(tag=tag, name='country')
                    cc_obj.value = country_code
                    cc_obj.save()
                    lat_obj, created = TagProps.objects.get_or_create(tag=tag, name='lat')
                    lat_obj.value = lat
                    lat_obj.save()
                    lng_obj, created = TagProps.objects.get_or_create(tag=tag, name='lng')
                    lng_obj.value = lng
                    lng_obj.save()
