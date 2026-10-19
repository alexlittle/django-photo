"""
Management command to pre-generate sorl thumbnails for all photos.

Running this avoids the slow first load of album pages, since thumbnails
are normally generated on demand when a page is rendered.

By default it generates the sizes used by the templates (250, 300, 700).
Sizes can be overridden with --sizes, and generation can be limited to a
single album with --album.
"""

from django.core.management.base import BaseCommand

from photo.models import Album, Photo

DEFAULT_SIZES = [250, 300]
PROGRESS_EVERY = 100


class Command(BaseCommand):
    help = "Pre-generate sorl thumbnails for all photos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sizes",
            dest="sizes",
            default=",".join(str(s) for s in DEFAULT_SIZES),
            help="Comma-separated list of thumbnail widths to generate "
            f"(default: {','.join(str(s) for s in DEFAULT_SIZES)}).",
        )
        parser.add_argument(
            "--album",
            dest="album",
            default=None,
            help="Only generate thumbnails for photos in the album with this name.",
        )

    def handle(self, *args, **options):
        sizes = []
        for raw in options["sizes"].split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                sizes.append(int(raw))
            except ValueError:
                self.stderr.write(self.style.WARNING(f"Ignoring invalid thumbnail size: {raw}"))

        if not sizes:
            self.stderr.write(self.style.ERROR("No valid thumbnail sizes given."))
            return

        album = None
        if options["album"]:
            try:
                album = Album.objects.get(name=options["album"])
            except Album.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Album not found: {options['album']}"))
                return

        photos = Photo.objects.all()
        if album is not None:
            photos = photos.filter(album=album)

        total = photos.count()
        self.stdout.write(f"Generating thumbnails for {total} photo(s), sizes: {sizes}")

        generated = 0
        failed = 0
        for index, photo in enumerate(photos.iterator(), start=1):
            for size in sizes:
                try:
                    # Force sorl to generate and cache the thumbnail.
                    photo.get_thumbnail(size)
                    generated += 1
                except Exception as exc:  # noqa: BLE001 - report and continue
                    failed += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"Failed thumbnail size {size} for photo {photo.id} "
                            f"({photo.file}): {exc}"
                        )
                    )

            if index % PROGRESS_EVERY == 0 or index == total:
                self.stdout.write(f"  processed {index}/{total} photos...")

        self.stdout.write(
            self.style.SUCCESS(f"Done. Generated {generated} thumbnail(s), {failed} failed.")
        )
