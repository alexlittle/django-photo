"""Shared fixtures and helpers for the photo app view tests."""

import os
import re
import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from photo.models import Album, Photo, PhotoProps, PhotoTag, Tag, TagProps


def make_datetime(year, month, day, hour=12, minute=30):
    """Build a datetime that matches the project's USE_TZ setting."""
    value = datetime(year, month, day, hour, minute)  # noqa: DTZ001 - made aware below
    if settings.USE_TZ:
        value = timezone.make_aware(value)
    return value


def local(value):
    """Normalise a stored datetime back to local time for assertions."""
    return timezone.localtime(value) if settings.USE_TZ else value


def create_album(name, **kwargs):
    return Album.objects.create(name=name, **kwargs)


def create_tag(name, category=None):
    """Tag.save() derives the slug from the name on first save."""
    return Tag.objects.create(name=name, tagcategory=category)


def set_tag_prop(tag, name, value):
    """TagProps has a unique_together on (tag, name), so update rather than add."""
    TagProps.objects.update_or_create(tag=tag, name=name, defaults={"value": value})


def create_photo(album, file, date=None, **kwargs):
    return Photo.objects.create(
        album=album,
        file=file,
        date=date if date is not None else make_datetime(2024, 1, 1),
        **kwargs,
    )


def set_photo_prop(photo, name, value):
    PhotoProps.objects.update_or_create(photo=photo, name=name, defaults={"value": value})


def tag_photo(photo, *tags):
    for tag in tags:
        PhotoTag.objects.get_or_create(photo=photo, tag=tag)


def set_site_domain(domain):
    """Point the configured Django site (django.contrib.sites) at ``domain``.

    Commands build their links from ``photo.lib.get_domain()``, which reads
    ``Site.objects.get_current().domain`` -- this is the test-side equivalent
    of the old ``override_settings(DOMAIN_NAME=...)``.
    """
    Site.objects.update_or_create(pk=settings.SITE_ID, defaults={"domain": domain, "name": domain})


class PhotoRootTestCase(TestCase):
    """A TestCase with ``settings.PHOTO_ROOT`` pointed at a throwaway directory.

    Anything that touches the filesystem should inherit from this: the two image
    views, the album move branch of ``PhotoUpdateTagsView``, the directory check
    in ``ScanFolderForm``, and the ``post_delete`` handler on ``Photo``.
    """

    def setUp(self):
        super().setUp()
        self.photo_root = tempfile.mkdtemp(prefix="photo-tests-")
        self.addCleanup(shutil.rmtree, self.photo_root, ignore_errors=True)
        overrides = override_settings(PHOTO_ROOT=self.photo_root)
        overrides.enable()
        self.addCleanup(overrides.disable)

    def album_dir(self, album):
        """Create and return the on-disk directory for an album."""
        path = os.path.join(self.photo_root, album.get_safe_name())
        os.makedirs(path, exist_ok=True)
        return path

    def image_path(self, photo):
        return os.path.join(self.photo_root, photo.album.get_safe_name(), photo.file)

    def write_image(self, photo, mode="RGB", size=(40, 40), image_format="JPEG"):
        """Write a real (tiny) image where the views will look for it."""
        colour = (200, 40, 40) if mode == "RGB" else (200, 40, 40, 255)
        path = os.path.join(self.album_dir(photo.album), photo.file)
        Image.new(mode, size, colour).save(path, image_format)
        return path

    def write_image_with_exif(self, photo, size=(40, 40), **exif_tags):
        """Write a JPEG carrying real EXIF tags, given by numeric tag id.

        Useful ids: 36867 DateTimeOriginal, 36868 DateTimeDigitized,
        306 DateTime. Values use the EXIF format "YYYY:MM:DD HH:MM:SS".
        """
        exif = Image.Exif()
        for tag_id, value in exif_tags.items():
            exif[int(tag_id)] = value
        path = os.path.join(self.album_dir(photo.album), photo.file)
        Image.new("RGB", size, (200, 40, 40)).save(path, "JPEG", exif=exif)
        return path


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    """Drop ANSI colour escape sequences so assertions read normally."""
    return ANSI_ESCAPE.sub("", text)


class CommandTestCase(PhotoRootTestCase):
    """Base for management command tests.

    The commands write via ``self.stdout.write`` (styled with ``self.style``),
    and a couple still use bare ``print()`` (e.g. interactive prompts).
    ``run_command`` redirects ``sys.stdout`` *and* passes the same buffer as
    the command's stdout/stderr, so both styles are captured either way.
    """

    def run_command(self, name, *args, **options):
        buffer = StringIO()
        options.setdefault("stdout", buffer)
        options.setdefault("stderr", buffer)
        with redirect_stdout(buffer):
            call_command(name, *args, **options)
        return strip_ansi(buffer.getvalue())
