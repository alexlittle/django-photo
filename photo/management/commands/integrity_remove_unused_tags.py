
"""
Management command to clean up any unused tags
"""
from django.core.management.base import BaseCommand

from photo.models import Tag

from . import bcolors


class Command(BaseCommand):
    help = "Removes any unused tags"

    def handle(self, *args, **options):
        tags = Tag.objects.filter(phototag=None)
        
        print("Unused tags")
        print("---------------------------------------")
        counter = tags.count()
        
        for t in tags:
            print("Removing: " + t.name)
            t.delete()
            
        if counter == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d unused tags removed %s" % (bcolors.WARNING, counter, bcolors.ENDC))
        print("---------------------------------------")
