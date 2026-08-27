from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.lib import get_domain
from photo.models import Tag


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        tags = Tag.objects.filter(tagcategory__name="Location")

        self.stdout.write("Missing coordinates")
        self.stdout.write("---------------------------------------")

        counter = 0
        for t in tags:
            if t.get_lat() is None or t.get_lat() == "0":
                counter += 1
                tag_link = reverse("admin:photo_tag_change", args=(t.id,))
                tag_slug = reverse("photo:tag_slug", args=(t.slug,))
                self.stdout.write(f"{counter} {t.name} - {get_domain()}{tag_link}")
                self.stdout.write(f"     {get_domain()}{tag_slug}")

        if counter == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{counter} missing coordinates"))
        self.stdout.write("---------------------------------------")
