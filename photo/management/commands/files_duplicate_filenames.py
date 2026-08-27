"""
Management command to find photos with same filename
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count

from photo.models import Photo


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        self.stdout.write("Photos with same filename")
        self.stdout.write("---------------------------------------")

        results = Photo.objects.values("file").annotate(count=Count("file")).order_by("count")

        counter = 0
        total_duplicates = 0
        for result in results:
            if result["count"] > 1:
                url = "{}admin/photo/photo/?q={}".format(settings.DOMAIN_NAME, result["file"])
                self.stdout.write(f"{result['count']} duplicates of {result['file']} - {url}")
                counter += 1
                total_duplicates += result["count"]

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(
                self.style.WARNING(
                    f"{counter} photos with duplicate filenames "
                    f"(total {total_duplicates} duplicates)"
                )
            )
        self.stdout.write("---------------------------------------")
