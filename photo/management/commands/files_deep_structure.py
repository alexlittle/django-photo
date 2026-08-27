"""
Management command to find albums with deep directory structure
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from photo.models import Album


class Command(BaseCommand):
    help = "Finds albums with deep directory structure"

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--count",
            required=True,
            help="max_dirs",
        )

    def handle(self, *args, **options):
        try:
            max_dirs = int(options["count"])
        except ValueError:
            raise CommandError(f"Invalid count {options['count']!r}, expected an integer") from None
        self.stdout.write(f"Finds albums deeper than {max_dirs} directories")
        self.stdout.write("---------------------------------------")
        counter = 0
        for album in Album.objects.all():
            dirs = filter(None, album.name.split("/"))
            if len(list(dirs)) > max_dirs:
                link = reverse("photo:album", args=(album.id,))
                self.stdout.write(f"{settings.DOMAIN_NAME}{link} - {album.title} [{album.name}]")
                counter += 1
        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} directories deeper than {max_dirs}"))
        self.stdout.write("---------------------------------------")
