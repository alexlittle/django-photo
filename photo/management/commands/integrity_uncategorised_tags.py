"""
Management command to get tags with no category set
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Tag

from . import bcolors


class Command(BaseCommand):
    help = "Finds all uncategorised tags"

    def handle(self, *args, **options):
        print("Uncategorised tags")
        print("---------------------------------------")

        tags = Tag.objects.filter(tagcategory=None)
        for t in tags:
            link = reverse("admin:photo_tag_change", args=(t.id,))
            print(f"{t.name} - {settings.DOMAIN_NAME}{link}")

        if tags.count() == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{tags.count()} uncategorised tags{bcolors.ENDC}")
        print("---------------------------------------")
