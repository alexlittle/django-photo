from django.core.management.base import BaseCommand

from photo.models import Album, Photo, PhotoTag, Tag, TagCategory


class Command(BaseCommand):
    help = "Retags dates"

    def add_arguments(self, parser):
        parser.add_argument(
            "-a",
            "--album",
            dest="album",
            required=True,
            help="Source Album",
        )

    def handle(self, *args, **options):
        album = Album.objects.get(pk=options["album"])
        photos = Photo.objects.filter(album=album)
        date_category, _ = TagCategory.objects.get_or_create(name="Date")

        print(f"Retagging date tags for {album.title}")
        print("---------------------------------------")

        # remove existing date tags for the whole album in one go
        PhotoTag.objects.filter(photo__in=photos, tag__tagcategory__name="Date").delete()

        tag_cache = {}

        def get_date_tag(name):
            if name not in tag_cache:
                tag_cache[name], _ = Tag.objects.get_or_create(
                    name=name, defaults={"tagcategory": date_category}
                )
            return tag_cache[name]

        new_photo_tags = []
        for p in photos:
            print(p)
            year_tag = get_date_tag(p.date.year)
            month_tag = get_date_tag(p.date.strftime("%B"))
            new_photo_tags.append(PhotoTag(photo=p, tag=year_tag))
            new_photo_tags.append(PhotoTag(photo=p, tag=month_tag))
            print(f"Added date tags: {year_tag.name} {month_tag.name}")

        PhotoTag.objects.bulk_create(new_photo_tags)
