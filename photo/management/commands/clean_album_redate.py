from datetime import date, datetime, time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from photo.models import Album, Photo


class Command(BaseCommand):
    help = "Redates photos"

    def add_arguments(self, parser):
        parser.add_argument("date")
        parser.add_argument(
            "-a",
            "--album",
            dest="album",
            required=True,
            help="Source Album",
        )

    def handle(self, *args, **options):
        date_str = options["date"]
        parts = date_str.split("-")
        try:
            year, month, day = (int(part) for part in parts)
        except (IndexError, ValueError) as exc:
            raise CommandError(f"Invalid date {date_str!r}, expected YYYY-MM-DD") from exc
        new_date = timezone.make_aware(datetime.combine(date(year, month, day), time.min))
        album = Album.objects.get(pk=options["album"])
        photos = Photo.objects.filter(album=album)
        for p in photos:
            p.date = new_date
            p.save()
