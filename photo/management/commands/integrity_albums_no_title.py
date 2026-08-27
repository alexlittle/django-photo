"""
Management command to find albums with no title set
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Length
from django.urls import reverse

from photo.lib import get_domain
from photo.models import Album


class Command(BaseCommand):
    help = "find albums with no title set"

    def handle(self, *args, **options):
        # Length(), not title="", so this can't be fooled by a MySQL "PAD
        # SPACE" collation treating "" and " " as equal (see utf8mb4_unicode_ci
        # in CI's test DB vs utf8mb4_0900_ai_ci locally).
        albums = Album.objects.annotate(title_len=Length("title")).filter(
            Q(title=None) | Q(title_len=0)
        )

        self.stdout.write("Albums with no title")
        self.stdout.write("---------------------------------------")

        counter = 0
        for a in albums:
            link = reverse("photo:album", args=(a.id,))
            self.stdout.write(f"{a.name} - {get_domain()}{link}")
            counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums without a title"))
        self.stdout.write("---------------------------------------")
