
"""
Management command to rename files
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Album

class Command(BaseCommand):
    help = "Checks for folders that aren't in the database"


    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--dir',
            dest='dir',
            help='Source directory',
        )
        

    def rename(self, file):
        new_file = file.replace('(','')
        new_file = new_file.replace(')','')
        new_file = new_file.replace('&','and')
        new_file = new_file.replace(' ','-')
        new_file = new_file.replace('--','-')
        new_file = new_file.lower()
        return new_file
    
    def handle(self, *args, **options): 
        scan_dir = options['dir']
        print(scan_dir)  
        
        list_of_files = list()
        for (dirpath, dirnames, filenames) in os.walk(scan_dir):
            list_of_files += [os.path.join(dirpath, file) for file in filenames]
        
        for elem in list_of_files:
            new_file = self.rename(elem) 
            print(elem + " > " + new_file)    
            os.rename(elem, new_file)
