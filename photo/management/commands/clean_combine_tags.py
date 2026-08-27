"""
Management command to combine tags
"""

from django.core.management.base import BaseCommand

from photo.models import PhotoTag, Tag


class Command(BaseCommand):
    help = "Combines tags"

    def add_arguments(self, parser):
        parser.add_argument("oldtag", type=str)
        parser.add_argument("newtag", type=str)

    def handle(self, *args, **options):
        oldtag = Tag.objects.get(slug=options["oldtag"])
        newtag = Tag.objects.get(slug=options["newtag"])

        if oldtag.id == newtag.id:
            self.stdout.write(self.style.ERROR("Cannot combine a tag with itself"))
            return

        photo_tags = PhotoTag.objects.filter(tag=oldtag)
        pt_count = photo_tags.count()
        for pt in photo_tags:
            PhotoTag.objects.get_or_create(photo=pt.photo, tag=newtag)

        oldtag.delete()

        print(f"{pt_count} tags replaced {options['oldtag']}")
