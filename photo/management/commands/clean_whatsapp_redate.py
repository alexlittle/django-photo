import datetime

from django.core.management.base import BaseCommand

from photo.models import Photo, PhotoTag, Tag, TagCategory


class Command(BaseCommand):
    help = "Checks for photos where date doesn't match"

    def add_arguments(self, parser):
        parser.add_argument("album")

    def handle(self, *args, **options):

        photos = Photo.objects.filter(file__istartswith="img-", album__pk=options["album"])
        date_category, _ = TagCategory.objects.get_or_create(name="Date")
        for p in photos:
            print(p.file + " : " + str(p.date))

            try:
                year = int(p.file[4:8])
                month = int(p.file[8:10])
                day = int(p.file[10:12])
            except ValueError:
                print(f"Skipping {p.file}: no date found in filename")
                continue

            if year != p.date.year or month != p.date.month or day != p.date.day:
                old_year = p.date.year
                old_month = p.date.strftime("%B")

                new_date = datetime.date(year, month, day)
                p.date = new_date
                p.save()

                # remove stale year/month tags from the photo's previous date
                PhotoTag.objects.filter(photo=p, tag__name__in=[str(old_year), old_month]).delete()

                # add year and month tags
                year_tag, _ = Tag.objects.get_or_create(
                    name=p.date.year, defaults={"tagcategory": date_category}
                )
                PhotoTag.objects.get_or_create(photo=p, tag=year_tag)

                month_tag, _ = Tag.objects.get_or_create(
                    name=p.date.strftime("%B"), defaults={"tagcategory": date_category}
                )
                PhotoTag.objects.get_or_create(photo=p, tag=month_tag)
