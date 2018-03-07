
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
from django.core.urlresolvers import reverse

class Command(BaseCommand):
    help = "gets lat/lng for places"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        tags = Tag.objects.filter(tagcategory__name='Place').exclude(tagprops__name='lat')
        print tags.count()
        for tag in tags[:50]:
            print tag.name
            try:
                url = 'http://api.geonames.org/searchJSON?q=%s&username=%s&maxRows=5' % (urllib.quote_plus(tag.name), 'alexlittle')
                print url
                u = urllib2.urlopen(urllib2.Request(url), timeout=10)
            
                data = u.read()  
                dataJSON = json.loads(data,"utf-8")
            
                print dataJSON['geonames'][0]
                accept = raw_input("Accept this? y/i/n")
                if accept == 'y':
                    print 'accepted'
                    lat = dataJSON['geonames'][0]['lat']
                    lng = dataJSON['geonames'][0]['lng']
                    TagProps(tag=tag, name='lat',value=lat).save()
                    TagProps(tag=tag, name='lng',value=lng).save()
                if accept =='i':
                    print 'ignore'
                    TagProps(tag=tag, name='lat',value=0).save()
                    TagProps(tag=tag, name='lng',value=0).save() 
                if accept =='n':
                    print 'no'
                    TagProps(tag=tag, name='lat',value=0).save()
                    TagProps(tag=tag, name='lng',value=0).save()
            except IndexError:
                TagProps(tag=tag, name='lat',value=0).save()
                TagProps(tag=tag, name='lng',value=0).save()
            except KeyError:
                TagProps(tag=tag, name='lat',value=0).save()
                TagProps(tag=tag, name='lng',value=0).save()
            
            
            
        