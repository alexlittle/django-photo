"""
Management command to clean up any unused tags
"""

from django.core.management.base import BaseCommand

from photo.models import Tag


class Command(BaseCommand):
    help = "Removes any unused tags"

    def handle(self, *args, **options):
        tags = Tag.objects.filter(phototag=None)

        self.stdout.write("Unused tags")
        self.stdout.write("---------------------------------------")
        counter = tags.count()

        for t in tags:
            self.stdout.write("Removing: " + t.name)
            t.delete()

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} unused tags removed"))
        self.stdout.write("---------------------------------------")
