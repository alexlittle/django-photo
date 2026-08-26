from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Tag, TagProps


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        tags = Tag.objects.filter(tagcategory__name="Location")

        print("Missing sources")
        print("---------------------------------------")

        counter = 0
        for t in tags:
            if t.get_prop("source") is None or t.get_prop("source") == "":
                counter += 1
                tag_link = reverse("admin:photo_tag_change", args=(t.id,))
                tag_slug = reverse("photo:tag_slug", args=(t.slug,))
                print(f"{counter} {t.name} - {settings.DOMAIN_NAME}{tag_link}")
                print(f"     {settings.DOMAIN_NAME}{tag_slug}")

                accept = input("Enter source [0 to ignore]")

                if accept != "0":
                    cc_obj, _ = TagProps.objects.get_or_create(tag=t, name="source")
                    cc_obj.value = accept
                    cc_obj.save()
