"""Tests for video support: scanning, creation date and poster-frame thumbnails."""

import os
import shutil
import subprocess
import tempfile
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from unittest import skipUnless

from django.core.management import call_command
from django.test import override_settings
from PIL import Image

from photo import video
from photo.models import Album, Photo
from tests.base import PhotoRootTestCase, create_album, create_photo, local

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def make_clip(path, seconds=2, creation_time=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=red:s=64x48:d={seconds}"]
    if creation_time:
        cmd += ["-metadata", f"creation_time={creation_time}"]
    subprocess.run([*cmd, path], check=True)


class IsVideoTests(PhotoRootTestCase):
    def test_matches_known_extensions_case_insensitively(self):
        self.assertTrue(video.is_video("a.mp4"))
        self.assertTrue(video.is_video("A.MOV"))

    def test_images_are_not_videos(self):
        self.assertFalse(video.is_video("a.jpg"))

    def test_photo_exposes_is_video(self):
        photo = create_photo(create_album("/2024/"), "clip.mp4")
        self.assertTrue(photo.is_video)


@skipUnless(HAS_FFMPEG, "ffmpeg not installed")
class VideoFileTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        media = tempfile.mkdtemp(prefix="photo-media-")
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        overrides = override_settings(MEDIA_ROOT=media)
        overrides.enable()
        self.addCleanup(overrides.disable)

    def upload(self, directory, **options):
        options.setdefault("defaulttags", "")
        with redirect_stdout(StringIO()):
            call_command("upload_album", directory=directory, stdout=StringIO(), **options)

    def test_scan_picks_up_videos(self):
        make_clip(os.path.join(self.photo_root, "2024", "clip.mp4"))

        self.upload("/2024/")

        self.assertTrue(Photo.objects.filter(file="clip.mp4", album__name="/2024/").exists())

    def test_scan_uses_container_creation_time(self):
        make_clip(
            os.path.join(self.photo_root, "2024", "clip.mp4"),
            creation_time="2023-07-04T10:20:30Z",
        )

        self.upload("/2024/")

        photo = Photo.objects.get(file="clip.mp4")
        self.assertEqual(local(photo.date).date().isoformat(), "2023-07-04")

    def test_scan_falls_back_to_default_date_without_metadata(self):
        make_clip(os.path.join(self.photo_root, "2024", "clip.mp4"))

        self.upload("/2024/", defaultdate=date(2022, 3, 5))

        photo = Photo.objects.get(file="clip.mp4")
        self.assertEqual(local(photo.date).date().isoformat(), "2022-03-05")

    def test_thumbnail_source_is_a_jpeg_frame(self):
        album = Album.objects.create(name="/2024/")
        make_clip(os.path.join(self.photo_root, "2024", "clip.mp4"))
        photo = create_photo(album, "clip.mp4")

        source = photo.get_thumbnail_source()

        self.assertNotEqual(source, photo.get_full_url())
        with Image.open(source) as im:
            self.assertEqual(im.format, "JPEG")

    def test_very_short_clip_still_gets_a_frame(self):
        album = Album.objects.create(name="/2024/")
        make_clip(os.path.join(self.photo_root, "2024", "tiny.mp4"), seconds=0.2)
        photo = create_photo(album, "tiny.mp4")

        self.assertTrue(os.path.exists(photo.get_thumbnail_source()))

    def test_deleting_the_photo_removes_the_frame(self):
        album = Album.objects.create(name="/2024/")
        make_clip(os.path.join(self.photo_root, "2024", "clip.mp4"))
        photo = create_photo(album, "clip.mp4")
        frame = photo.get_thumbnail_source()

        with redirect_stdout(StringIO()):
            photo.delete()

        self.assertFalse(os.path.exists(frame))

    def test_unreadable_video_falls_back_to_the_file_path(self):
        album = Album.objects.create(name="/2024/")
        path = os.path.join(self.photo_root, "2024", "bad.mp4")
        os.makedirs(os.path.dirname(path))
        with open(path, "wb") as fh:
            fh.write(b"not a video")
        photo = create_photo(album, "bad.mp4")

        self.assertEqual(photo.get_thumbnail_source(), photo.get_full_url())
