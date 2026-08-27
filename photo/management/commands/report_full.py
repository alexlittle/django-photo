from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        # deep structure
        call_command("files_deep_structure", count=2)

        # Missing albums (not in db but on disk)
        call_command("files_scan_albums")

        # Missing photos (not in db but on disk)
        call_command("files_scan_photos", files=True)

        # Missing photos (in db but not disk)
        call_command("files_scan_photos", db=True)

        # duplicate photo filenames
        call_command("files_duplicate_filenames")

        # Uncategorised tags
        call_command("integrity_uncategorised_tags")

        # remove unused tags -- runs after the uncategorised-tags report above,
        # so a tag removed here still showed up in that report first
        call_command("integrity_remove_unused_tags")

        # Album cover issues
        call_command("integrity_album_covers")

        # Album without titles
        call_command("integrity_albums_no_title")

        # Photos with only 1 tag
        call_command("integrity_only_one_tag")

        # Small albums
        call_command("integrity_small_albums", count=10)

        # remove empty albums
        call_command("integrity_remove_empty_albums")

        # locations without coordinates
        call_command("report_missing_coordinates")

        # locations without source
        call_command("report_missing_source")

        # tag diff
        call_command("tag_diff")

        # Note: report_missing_country is deliberately not run here -- it
        # blocks on input(), which would hang report_full when run
        # unattended (e.g. from cron). Run it separately when wanted.
