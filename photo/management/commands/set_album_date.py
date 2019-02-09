
"""
Management command to auto add album date
"""
import datetime
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Album

class Command(BaseCommand):
    help = "Add album date"


    def add_arguments(self, parser):
        pass
        

    def handle(self, *args, **options):
        albums = Album.objects.filter(date_display=None)
        for a in albums:
            parts = a.name.split('/')
            print(a.name)
            date_parts = parts[2].split('-')
            try:
                display_date = datetime.datetime(int(date_parts[0]),int(date_parts[1]),1,0,0,0).strftime('%B %Y')
                a.date_display = display_date
                a.save()
            except IndexError:
                pass
            except ValueError:
                pass
            