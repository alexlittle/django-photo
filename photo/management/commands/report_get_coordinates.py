
"""
Management command to get lat/lng for places
"""
import urllib
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Tag, TagProps


class Command(BaseCommand):
    help = "gets lat/lng for places"

    def handle(self, *args, **options):
        places = Tag.objects.filter(
            tagcategory__name='Location')
        
        tags = []
        for place in places:
            try:
                lat = TagProps.objects.get(tag=place, name='lat')
                if lat.value == '0':
                    tags.append(place)
            except TagProps.DoesNotExist:
                tags.append(place)
                
        print(len(tags))
        for tag in tags:
            print("--------------------")
            print(tag.name)
            print("Edit: %sadmin/photo/tag/%d/change/" % (settings.DOMAIN_NAME, tag.id))
            print("Photos: %stag/%s" % (settings.DOMAIN_NAME, tag.slug))
            params = {
                'q': urllib.parse.quote_plus(tag.name.encode('utf-8')),
                'username': settings.GEONAMES_USERNAME,
                'maxRows': 5}
            if tag.get_prop('country'):
                params['country'] = tag.get_prop('country')

            url = 'http://api.geonames.org/searchJSON?' + \
                urllib.parse.urlencode(params)

            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            data_json = json.loads(response.read())
            
            
            
            if len(data_json['geonames']) > 0:
                for i in range(0,5):
                    try:
                        print("%d : %s" % (i, data_json['geonames'][i]))
                    except (IndexError, KeyError):
                        pass
                accept = input("Accept this? [0-4/Ignore/No]")
                
                if accept == 'i':
                    print('ignoring')
                elif accept == 'n':
                    print('no')
                else:
                    idx = int(accept)
                    print('accepted')
                    lat = data_json['geonames'][idx]['lat']
                    lng = data_json['geonames'][idx]['lng']
                    lat_obj, created = TagProps.objects.get_or_create(tag=tag, name='lat')
                    lat_obj.value = lat
                    lat_obj.save()
                    lng_obj, created = TagProps.objects.get_or_create(tag=tag, name='lng')
                    lng_obj.value = lng
                    lng_obj.save()
