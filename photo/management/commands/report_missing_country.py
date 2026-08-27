from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.lib import get_domain
from photo.models import Tag, TagProps


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        tags = Tag.objects.filter(tagcategory__name="Location")

        print("Missing countries")
        print("---------------------------------------")

        counter = 0
        for t in tags:
            if t.get_prop("country") is None or t.get_prop("country") == "":
                counter += 1
                tag_link = reverse("admin:photo_tag_change", args=(t.id,))
                tag_slug = reverse("photo:tag_slug", args=(t.slug,))
                print(f"{counter} {t.name} - {get_domain()}{tag_link}")
                print(f"     {get_domain()}{tag_slug}")
                accept = input("Enter country code? [0 to ignore]")

                if accept != "0":
                    country_code = accept
                    print(country_code)
                    cc_obj, _ = TagProps.objects.get_or_create(tag=t, name="country")
                    cc_obj.value = country_code
                    cc_obj.save()
