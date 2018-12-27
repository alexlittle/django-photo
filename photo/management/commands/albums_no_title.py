
"""
Management command to find albums with no title set
"""
import datetime
import os
import time 
import django.db.models


from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse

from photo.models import Album

class Command(BaseCommand):
    help = "find albums with no title set"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        albums = Album.objects.filter(title=None)
        counter = 0
        for a in albums:
            print a.name + " - http://localhost.photo" + reverse('photo_album', args=(a.id,))
            counter += 1
                
        print counter