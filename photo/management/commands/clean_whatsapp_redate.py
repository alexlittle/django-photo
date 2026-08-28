from datetime import date, datetime, time

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from photo.models import Photo, PhotoTag, Tag, TagCategory


class Command(BaseCommand):
    help = "Checks for photos where date doesn't match"

    def add_arguments(self, parser):
        parser.add_argument("album")

    def handle(self, *args, **options):

        photos = Photo.objects.filter(file__istartswith="img-", album__pk=options["album"])
        date_category, _ = TagCategory.objects.get_or_create(name="Date")
        tag_cache = {}

        def get_date_tag(name):
            if name not in tag_cache:
                tag_cache[name], _ = Tag.objects.get_or_create(
                    name=name, defaults={"tagcategory": date_category}
                )
            return tag_cache[name]

        changed_photos = []
        stale_tag_filter = Q()
        new_photo_tags = []

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

                p.date = timezone.make_aware(datetime.combine(date(year, month, day), time.min))
                changed_photos.append(p)

                # remove stale year/month tags from the photo's previous date
                stale_tag_filter |= Q(photo=p, tag__name__in=[str(old_year), old_month])

                # add year and month tags
                year_tag = get_date_tag(p.date.year)
                month_tag = get_date_tag(p.date.strftime("%B"))
                new_photo_tags.append(PhotoTag(photo=p, tag=year_tag))
                new_photo_tags.append(PhotoTag(photo=p, tag=month_tag))

        if changed_photos:
            Photo.objects.bulk_update(changed_photos, ["date"])
            PhotoTag.objects.filter(stale_tag_filter).delete()
            PhotoTag.objects.bulk_create(new_photo_tags, ignore_conflicts=True)
