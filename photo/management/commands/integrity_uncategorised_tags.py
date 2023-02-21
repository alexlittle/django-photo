
"""
Management command to get tags with no category set
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from photo.models import Tag
from django.urls import reverse

from . import bcolors


class Command(BaseCommand):
    help = "Finds all uncategorised tags"

    def handle(self, *args, **options):
        print("Uncategorised tags" )
        print("---------------------------------------")
            
        tags = Tag.objects.filter(tagcategory=None)
        for t in tags:
            print("%s - %s%s" % (t.name, settings.DOMAIN_NAME, reverse('admin:photo_tag_change', args=(t.id, ))))
        
        if tags.count() == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d uncategorised tags%s" % (bcolors.WARNING, tags.count(), bcolors.ENDC))
        print("---------------------------------------")
