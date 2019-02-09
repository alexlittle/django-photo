
"""
Management command to get lat/lng for places
"""
import os
import time 
import urllib
import urllib2 
import json
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import PhotoTag, Tag, TagProps
from django.urls import reverse

class Command(BaseCommand):
    help = "gets lat/lng for places"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        tags = Tag.objects.filter(tagcategory__name='Place').exclude(tagprops__name='lat')
        print(tags.count())
        for tag in tags:
            print(tag.name)
            try:
                params = {
                    'q': urllib.quote_plus(tag.name.encode('utf-8')),
                    'username': settings.GEONAMES_USERNAME,
                    'maxRows': 5}
                if tag.get_prop('country'):
                    params['country'] = tag.get_prop('country')
                    
                url = 'http://api.geonames.org/searchJSON?' + urllib.urlencode(params)
                print(url)

                u = urllib2.urlopen(urllib2.Request(url), timeout=10)
            
                data = u.read()  
                dataJSON = json.loads(data,"utf-8")
            
                print(dataJSON['geonames'][0])
                accept = raw_input("Accept this? [Yes/Ignore/No]")
                if accept == 'y':
                    print('accepted')
                    lat = dataJSON['geonames'][0]['lat']
                    lng = dataJSON['geonames'][0]['lng']
                    TagProps(tag=tag, name='lat',value=lat).save()
                    TagProps(tag=tag, name='lng',value=lng).save()
                if accept =='i':
                    print('ignoring')
                if accept =='n':
                    print('no')
                    TagProps(tag=tag, name='lat',value=0).save()
                    TagProps(tag=tag, name='lng',value=0).save()
            except IndexError:
                pass
                # TagProps(tag=tag, name='lat',value=0).save()
                # TagProps(tag=tag, name='lng',value=0).save()
            except KeyError:
                pass
                # TagProps(tag=tag, name='lat',value=0).save()
                # TagProps(tag=tag, name='lng',value=0).save()
            
            
            
        