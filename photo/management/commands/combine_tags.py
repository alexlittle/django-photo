
"""
Management command to combine tags
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import PhotoTag, Tag

class Command(BaseCommand):
    help = "Combines tags"


    def add_arguments(self, parser):
        parser.add_argument('keep_tag')
        parser.add_argument('replace_tag')
        

    def handle(self, *args, **options):
        keep_tag = Tag.objects.get(name=options['keep_tag'])
        replace_tag = Tag.objects.get(name=options['replace_tag'])
        
        photo_tags = PhotoTag.objects.filter(tag=replace_tag)
        for pt in photo_tags:
            pt.tag = keep_tag
            pt.save()
        
        