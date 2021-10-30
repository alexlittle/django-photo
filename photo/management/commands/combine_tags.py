
"""
Management command to combine tags
"""
from django.core.management.base import BaseCommand

from photo.models import PhotoTag, Tag


class Command(BaseCommand):
    help = "Combines tags"

    def add_arguments(self, parser):
        parser.add_argument(
                    '-kt',
                    '--keep_tag',
                    dest='keep_tag',
                    help='Tag to keep',
                )
        
        parser.add_argument(
                    '-rt',
                    '--replace_tag',
                    dest='replace_tag',
                    help='Tag to replace',
                )

    def handle(self, *args, **options):
        try:
            keep_tag = Tag.objects.get(name=options['keep_tag'])
        except Tag.DoesNotExist:
            print("Tag not found: %s" % options['keep_tag'])
            
        replace_tag = Tag.objects.get(name=options['replace_tag'])

        photo_tags = PhotoTag.objects.filter(tag=replace_tag)
        for pt in photo_tags:
            pt.tag = keep_tag
            pt.save()
