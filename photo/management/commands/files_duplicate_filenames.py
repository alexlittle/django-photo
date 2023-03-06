
"""
Management command to find photos with same filename
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Photo

from . import bcolors


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        print("Photos with same filename")
        print("---------------------------------------")
        
        results = Photo.objects.values('file').annotate(count=Count('file'))
        
        counter = 0
        for result in results:
            if result['count'] > 1:
                url = "{}admin/photo/photo/?q={}".format(settings.DOMAIN_NAME, result['file'])
                print("%d duplicates of %s - %s" % (result['count'], result['file'], url))
                counter += 1
        
        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d photos with duplicate filenames%s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")