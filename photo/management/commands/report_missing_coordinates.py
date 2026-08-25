from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Tag

from . import bcolors


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        tags = Tag.objects.filter(tagcategory__name="Location")

        print("Missing coordinates")
        print("---------------------------------------")

        counter = 0
        for t in tags:
            if t.get_lat() is None or t.get_lat() == "0":
                counter += 1
                tag_link = reverse("admin:photo_tag_change", args=(t.id,))
                tag_slug = reverse("photo:tag_slug", args=(t.slug,))
                print(f"{counter} {t.name} - {settings.DOMAIN_NAME}{tag_link}")
                print(f"     {settings.DOMAIN_NAME}{tag_slug}")

        if counter == 0:
            print(f"{bcolors.WARNING}OK{bcolors.ENDC}")
        else:
            print("---------------------------------------")
            print(f"{bcolors.WARNING}{counter} missing coordinates{bcolors.ENDC}")
        print("---------------------------------------")
