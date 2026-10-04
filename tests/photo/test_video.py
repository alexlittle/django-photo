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
from django.urls import reverse
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


@skipUnless(HAS_FFMPEG, "ffmpeg not installed")
class VideoViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        album = Album.objects.create(name="/2024/")
        self.path = os.path.join(self.photo_root, "2024", "clip.mp4")
        make_clip(self.path)
        self.photo = create_photo(album, "clip.mp4")
        self.size = os.path.getsize(self.path)
        self.url = reverse("photo:video", kwargs={"photo_id": self.photo.id})

    def body(self, response):
        return b"".join(response.streaming_content)

    def test_serves_the_whole_file(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "video/mp4")
        self.assertEqual(response["Accept-Ranges"], "bytes")
        with open(self.path, "rb") as fh:
            self.assertEqual(self.body(response), fh.read())

    def test_range_request_returns_partial_content(self):
        response = self.client.get(self.url, headers={"Range": "bytes=10-19"})

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Range"], f"bytes 10-19/{self.size}")
        with open(self.path, "rb") as fh:
            fh.seek(10)
            self.assertEqual(self.body(response), fh.read(10))

    def test_open_ended_and_suffix_ranges(self):
        response = self.client.get(self.url, headers={"Range": "bytes=5-"})
        self.assertEqual(response["Content-Range"], f"bytes 5-{self.size - 1}/{self.size}")

        response = self.client.get(self.url, headers={"Range": "bytes=-4"})
        self.assertEqual(len(self.body(response)), 4)

    def test_unsatisfiable_range_is_416(self):
        response = self.client.get(self.url, headers={"Range": f"bytes={self.size + 5}-"})

        self.assertEqual(response.status_code, 416)

    def test_non_video_is_404(self):
        photo = create_photo(Album.objects.get(name="/2024/"), "a.jpg")

        response = self.client.get(reverse("photo:video", kwargs={"photo_id": photo.id}))

        self.assertEqual(response.status_code, 404)

    def test_view_returns_the_poster_frame_for_a_video(self):
        response = self.client.get(reverse("photo:view", kwargs={"photo_id": self.photo.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")


@skipUnless(HAS_FFMPEG, "ffmpeg not installed")
class VideoWithOtherCommandsTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = Album.objects.create(name="/2024/")
        make_clip(
            os.path.join(self.photo_root, "2024", "clip.mp4"),
            creation_time="2023-07-04T10:20:30Z",
        )
        self.photo = create_photo(self.album, "clip.mp4")

    def test_redate_command_uses_video_metadata_and_does_not_crash(self):
        with redirect_stdout(StringIO()):
            call_command("clean_redate_photos", album=str(self.album.id))

        self.photo.refresh_from_db()
        self.assertEqual(local(self.photo.date).date().isoformat(), "2023-07-04")

    def test_rewrite_exif_command_skips_videos(self):
        with redirect_stdout(StringIO()) as out:
            call_command("clean_rewrite_exif_data", album=str(self.album.id))

        self.assertNotIn("error", out.getvalue().lower())

    def test_album_page_and_edit_page_render(self):
        response = self.client.get(reverse("photo:album", kwargs={"album_id": self.album.id}))
        self.assertContains(response, "video-badge")
        self.assertContains(response, reverse("photo:video", kwargs={"photo_id": self.photo.id}))

        response = self.client.get(reverse("photo:edit", kwargs={"photo_id": self.photo.id}))
        self.assertContains(response, "<video")
