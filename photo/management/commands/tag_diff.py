import difflib
import re

from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from photo.models import Tag

from . import bcolors

class Command(BaseCommand):
    help = _(u"Check for tags that are very similar")
    errors = []

    def add_arguments(self, parser):
        parser.add_argument('cutoff', type=float, default=0.85, nargs='?')

    def regex_tag_matches(self, tag1, tag2):
        for itr in settings.IGNORE_TAG_REGEXS:
            p = re.compile(itr)
            if p.match(tag1) and p.match(tag2):
                return True
        return False

    def handle(self, *args, **options):

        print("Tag diff")
        print("---------------------------------------")

        cutoff = options['cutoff']

        # get all tags as plain list
        tags = list(Tag.objects.order_by('name').values_list('name', flat=True))

        match_count = 0
        for current_tag in tags:

            filtered_list = [tag for tag in tags if tag != current_tag]
            matches = difflib.get_close_matches(current_tag, filtered_list, cutoff=cutoff)

            filtered_matches = []
            for match in matches:
                if not self.regex_tag_matches(current_tag, match):
                    filtered_matches.append(match)

            url = settings.DOMAIN_NAME + reverse('photo:tag_slug', kwargs={'slug': slugify(current_tag)})
            if filtered_matches:
                print(f"{current_tag} - {url}")
                print(filtered_matches)
                print("----------------")
                match_count += 1


        if match_count == 0:
            print("%sOK%s" % (bcolors.OK, bcolors.ENDC))
        else:
            print("---------------------------------------")
            print("%s%d tags close to others%s" % (bcolors.WARNING, match_count, bcolors.ENDC))