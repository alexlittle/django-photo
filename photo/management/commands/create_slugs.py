
"""
Management command to create slugs
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Photo, Album, Tag,TagCategory

class Command(BaseCommand):
    help = "Create slugs"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        tag_categories = TagCategory.objects.filter(slug=None)
        for tc in tag_categories:
            print(tc.name)
            tc.save()
            
        tags = Tag.objects.filter(slug=None)
        for t in tags:
            print(t.name)
            t.save()
         
        albums = Album.objects.filter(slug=None)
        for a in albums:
            print(a.name)
            a.save()
            
        photos = Photo.objects.filter(slug=None)
        for p in photos:
            print(p.file)
            p.save()
            
            
            