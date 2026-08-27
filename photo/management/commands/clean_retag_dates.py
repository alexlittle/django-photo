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
        for p in photos:
            print(p)
            # remove existing date tags
            PhotoTag.objects.filter(photo=p, tag__tagcategory__name="Date").delete()

            year_tag, _ = Tag.objects.get_or_create(
                name=p.date.year, defaults={"tagcategory": date_category}
            )
            PhotoTag.objects.get_or_create(photo=p, tag=year_tag)

            month_tag, _ = Tag.objects.get_or_create(
                name=p.date.strftime("%B"), defaults={"tagcategory": date_category}
            )
            PhotoTag.objects.get_or_create(photo=p, tag=month_tag)
            print(f"Added date tags: {year_tag.name} {month_tag.name}")
