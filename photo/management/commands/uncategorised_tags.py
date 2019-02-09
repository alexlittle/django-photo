
"""
Management command to get tags with no category set
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import PhotoTag, Tag
from django.urls import reverse

class Command(BaseCommand):
    help = "Finds all uncategorised tags"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        tags = Tag.objects.filter(tagcategory=None)
        for t in tags:
            print("http://localhost.photo%s" % reverse('admin:photo_tag_change', args=(t.id, )))
            
        print(tags.count())
            
            
            
        