
"""
Management command to create pdf album
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.pdf import create_album

class Command(BaseCommand):
    help = "Creates pdf album"


    def add_arguments(self, parser):        
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):
        create_album.make(options['album'])
        