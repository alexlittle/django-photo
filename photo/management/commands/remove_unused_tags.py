
"""
Management command to clean up any unused tags
"""
from django.core.management.base import BaseCommand

from photo.models import Tag


class Command(BaseCommand):
    help = "Removes any unused tags"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        tags = Tag.objects.filter(phototag=None)
        for t in tags:
            print("Removing: " + t.name)
            t.delete()
