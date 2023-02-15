
"""
Management command to get tags with no category set
"""
from django.core.management.base import BaseCommand

from photo.models import Tag
from django.urls import reverse


class Command(BaseCommand):
    help = "Finds all uncategorised tags"

    def handle(self, *args, **options):
        tags = Tag.objects.filter(tagcategory=None)
        for t in tags:
            print("%s - http://localhost.photo%s" % (t.name,
                  reverse('admin:photo_tag_change', args=(t.id, ))))

        print(tags.count())
