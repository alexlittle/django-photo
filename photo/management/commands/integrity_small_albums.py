"""
Management command to find albums with less than X photos
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.urls import reverse

from photo.models import Album


class Command(BaseCommand):
    help = "Finds albums with less than X photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--count",
            required=True,
            help="max_count",
        )

    def handle(self, *args, **options):
        try:
            max_count = int(options["count"])
        except ValueError:
            raise CommandError(f"Invalid count {options['count']!r}, expected an integer") from None

        self.stdout.write(f"Albums with less than {max_count} photos")
        self.stdout.write("---------------------------------------")
        counter = 0

        for album in Album.objects.annotate(total=Count("photo")):
            if album.total < max_count:
                link = settings.DOMAIN_NAME + reverse("photo:album", args=(album.id,))
                self.stdout.write(f"{link} - {album.title} - {album.name} [{album.total} photos]")
                counter += 1

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(
                self.style.WARNING(f"{counter} albums with less than {max_count} photos")
            )
        self.stdout.write("---------------------------------------")
