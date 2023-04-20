
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from photo.models import Tag, TagProps

from . import bcolors


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
                print("%d %s - %s%s" % (counter,
                                        t.name,
                                        settings.DOMAIN_NAME,
                                        reverse('admin:photo_tag_change',
                                                args=(t.id, ))))
                print("     %s%s" % (settings.DOMAIN_NAME, reverse('photo_tag_slug', args=(t.slug,))))
                accept = input("Enter country code? [0 to ignore]")

                if accept != '0':
                    country_code = accept
                    print(country_code)
                    cc_obj, created = TagProps.objects.get_or_create(tag=t, name='country')
                    cc_obj.value = country_code
                    cc_obj.save()
