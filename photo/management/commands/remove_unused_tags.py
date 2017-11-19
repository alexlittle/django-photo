
"""
Management command to clean up any unused tags
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
    help = "Removes any unused tags"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        tags = Tag.objects.filter(phototag=None)
        for t in tags:
            print "Removing: " + t.name
            t.delete()
        