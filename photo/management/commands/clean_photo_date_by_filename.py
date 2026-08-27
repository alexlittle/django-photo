import datetime

from django.core.management.base import BaseCommand, CommandError

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
        date = options["date"].split("-")
        if len(date) != 3:
            raise CommandError(f"Invalid date {options['date']!r}, expected YYYY-MM-DD")
        try:
            year, month, day = (int(part) for part in date)
        except ValueError:
            raise CommandError(f"Invalid date {options['date']!r}, expected YYYY-MM-DD") from None

        album = Album.objects.get(pk=options["album"])
        photos = Photo.objects.filter(
            date__year=year, date__month=month, date__day=day, album=album
        )

        for photo in photos:
            try:
                new_year = int(photo.file[4:8])
                new_month = int(photo.file[8:10])
                new_day = int(photo.file[10:12])
                new_date = datetime.date(new_year, new_month, new_day)
            except ValueError:
                print(f"Skipping {photo.file}: no date found in filename")
                continue
            print(new_date)
            photo.date = new_date
            photo.save()
