"""
Management command to find photos with same filename
"""

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

        results = Photo.objects.values("file").annotate(count=Count("file")).order_by("count")

        counter = 0
        total_duplicates = 0
        for result in results:
            if result["count"] > 1:
                url = "{}admin/photo/photo/?q={}".format(settings.DOMAIN_NAME, result["file"])
                print(f"{result['count']} duplicates of {result['file']} - {url}")
                counter += 1
                total_duplicates += result["count"]

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(
                f"{bcolors.WARNING}{counter} photos with duplicate filenames "
                f"(total {total_duplicates} duplicates){bcolors.ENDC}"
            )
        print("---------------------------------------")
