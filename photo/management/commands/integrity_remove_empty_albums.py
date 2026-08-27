"""
Management command to clean up any albums with no photos
"""

from django.core.management.base import BaseCommand

from photo.models import Album


class Command(BaseCommand):
    help = "Removes any albums with no photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="List albums that would be removed, without removing them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        albums = Album.objects.filter(photo=None)

        self.stdout.write("Albums with no photos")
        self.stdout.write("---------------------------------------")
        counter = albums.count()

        for a in albums:
            if dry_run:
                self.stdout.write("Would remove: " + a.name)
            else:
                self.stdout.write("Removing: " + a.name)
                a.delete()

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        elif dry_run:
            self.stdout.write("---------------------------------------")
            self.stdout.write(
                self.style.WARNING(f"{counter} albums with no photos would be removed")
            )
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} albums with no photos removed"))
        self.stdout.write("---------------------------------------")
