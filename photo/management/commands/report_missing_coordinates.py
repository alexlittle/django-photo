import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Tag, TagCategory, TagProps

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        
        tags = Tag.objects.filter(tagcategory__name="Location")       
        
        
        counter = 0
        for t in tags:
            if t.get_lat() is None or t.get_lat() == "0":
                counter += 1
                print("%d %s - %s%s" % (counter,
                                        t.name,
                                        settings.DOMAIN_NAME,
                                        reverse('admin:photo_tag_change',
                                                args=(t.id, ))))
                print("     %s%s" % (settings.DOMAIN_NAME, reverse('photo_tag_slug',
                                                args=(t.slug,))))
                
        