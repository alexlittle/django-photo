import difflib
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo.models import Tag


class Command(BaseCommand):
    help = _("Check for tags that are very similar")
    errors = []

    def add_arguments(self, parser):
        parser.add_argument("cutoff", type=float, default=0.85, nargs="?")

    def regex_tag_matches(self, tag1, tag2):
        for itr in settings.IGNORE_TAG_REGEXS:
            p = re.compile(itr)
            if p.match(tag1) and p.match(tag2):
                return True
        return False

    def handle(self, *args, **options):

        self.stdout.write("Tag diff")
        self.stdout.write("---------------------------------------")

        cutoff = options["cutoff"]

        # get all tags as (name, slug) pairs
        tags = list(Tag.objects.order_by("name").values_list("name", "slug"))
        names = [name for name, _slug in tags]

        match_count = 0
        for current_tag, current_slug in tags:
            filtered_list = [name for name in names if name != current_tag]
            matches = difflib.get_close_matches(current_tag, filtered_list, cutoff=cutoff)

            filtered_matches = []
            for match in matches:
                if not self.regex_tag_matches(current_tag, match):
                    filtered_matches.append(match)

            url = settings.DOMAIN_NAME + reverse("photo:tag_slug", kwargs={"slug": current_slug})
            if filtered_matches:
                self.stdout.write(f"{current_tag} - {url}")
                self.stdout.write(str(filtered_matches))
                self.stdout.write("----------------")
                match_count += 1

        if match_count == 0:
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            self.stdout.write("---------------------------------------")
            self.stdout.write(self.style.WARNING(f"{match_count} tags close to others"))
