"""
Management command to create slugs
"""

from django.core.management.base import BaseCommand

from photo.models import Tag, TagCategory


class Command(BaseCommand):
    help = "Create slugs"

    def handle(self, *args, **options):
        tag_categories = TagCategory.objects.filter(slug="")
        for tc in tag_categories:
            print(tc.name)
            tc.save()

        tags = Tag.objects.filter(slug="")
        for t in tags:
            print(t.name)
            t.save()
