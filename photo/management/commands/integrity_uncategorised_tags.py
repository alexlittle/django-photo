"""
Management command to get tags with no category set
"""

from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.lib import get_domain
from photo.models import Tag


class Command(BaseCommand):
    help = "Finds all uncategorised tags"

    def handle(self, *args, **options):
        self.stdout.write("Uncategorised tags")
        self.stdout.write("---------------------------------------")

        tags = Tag.objects.filter(tagcategory=None)
        for t in tags:
            link = reverse("admin:photo_tag_change", args=(t.id,))
            self.stdout.write(f"{t.name} - {get_domain()}{link}")

        if tags.count() == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{tags.count()} uncategorised tags"))
        self.stdout.write("---------------------------------------")
