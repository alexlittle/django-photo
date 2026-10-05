"""Tests for video support: scanning, creation date, poster frames and playback.

ffmpeg/ffprobe are faked (``FakeFfmpeg``) so these run, and count towards coverage,
on machines without ffmpeg installed. One integration test at the bottom uses the
real binaries when they are available.
"""

import os
import shutil
import subprocess
import tempfile
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from unittest import skipUnless
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from PIL import Image

from photo import video
from photo.models import Album, Photo
from tests.base import PhotoRootTestCase, create_photo, local

HAS_FFMPEG = shutil.which("ffmpeg") is not None
CLIP_BYTES = bytes(range(256)) * 8  # 2048 bytes of recognisable content


class FakeFfmpeg:
    """Stand-in for subprocess.run covering the ffmpeg and ffprobe calls in photo.video."""

    def __init__(self, creation_time="", frame_ok=True):
        self.creation_time = creation_time
        self.frame_ok = frame_ok
        self.calls = []

    def __call__(self, cmd, **_kwargs):
        self.calls.append(cmd)
        if cmd[0] == "ffprobe":
            return subprocess.CompletedProcess(cmd, 0, stdout=self.creation_time + "\n")
        if self.frame_ok:
            Image.new("RGB", (64, 48), (200, 0, 0)).save(cmd[-1], "JPEG")
        return subprocess.CompletedProcess(cmd, 0, stdout="")


def write_clip(root, directory, name, content=CLIP_BYTES):
    path = os.path.join(root, directory, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


class IsVideoTests(SimpleTestCase):
    def test_matches_known_extensions_case_insensitively(self):
        self.assertTrue(video.is_video("a.mp4"))
        self.assertTrue(video.is_video("A.MOV"))

    def test_images_are_not_videos(self):
        self.assertFalse(video.is_video("a.jpg"))


class GetVideoDateTests(SimpleTestCase):
    def date_for(self, **kwargs):
        with patch("photo.video.subprocess.run", FakeFfmpeg(**kwargs)):
            return video.get_video_date("/x/clip.mp4")

    def test_parses_the_creation_time(self):
        parsed = self.date_for(creation_time="2023-07-04T10:20:30.000000Z")

        self.assertEqual(parsed.isoformat(), "2023-07-04T10:20:30+00:00")

    def test_no_creation_time_gives_none(self):
        self.assertIsNone(self.date_for(creation_time=""))

    def test_unparseable_value_gives_none(self):
        self.assertIsNone(self.date_for(creation_time="2023-99-99T99:99:99Z"))
        self.assertIsNone(self.date_for(creation_time="not a date"))

    def test_epoch_placeholder_gives_none(self):
        self.assertIsNone(self.date_for(creation_time="1970-01-01T00:00:00Z"))

    def test_naive_timestamp_gives_none(self):
        self.assertIsNone(self.date_for(creation_time="2023-07-04T10:20:30"))

    def test_missing_ffprobe_gives_none(self):
        with patch("photo.video.subprocess.run", side_effect=FileNotFoundError):
            self.assertIsNone(video.get_video_date("/x/clip.mp4"))


class PosterTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        media = tempfile.mkdtemp(prefix="photo-media-")
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        overrides = override_settings(MEDIA_ROOT=media)
        overrides.enable()
        self.addCleanup(overrides.disable)
        self.album = Album.objects.create(name="/2024/")
        write_clip(self.photo_root, "2024", "clip.mp4")
        self.photo = create_photo(self.album, "clip.mp4")

    def test_thumbnail_source_is_a_jpeg_frame(self):
        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            source = self.photo.get_thumbnail_source()

        self.assertNotEqual(source, self.photo.get_full_url())
        with Image.open(source) as im:
            self.assertEqual(im.format, "JPEG")

    def test_frame_is_only_extracted_once(self):
        fake = FakeFfmpeg()
        with patch("photo.video.subprocess.run", fake):
            self.photo.get_thumbnail_source()
            self.photo.get_thumbnail_source()

        self.assertEqual(len(fake.calls), 1)

    def test_images_use_the_file_itself(self):
        image = create_photo(self.album, "a.jpg")

        self.assertEqual(image.get_thumbnail_source(), image.get_full_url())

    def test_retries_from_the_start_when_the_first_seek_gives_no_frame(self):
        def run(cmd, **_kwargs):
            if cmd[cmd.index("-ss") + 1] == "1":  # nothing at 1s: clip is too short
                return subprocess.CompletedProcess(cmd, 0)
            Image.new("RGB", (8, 8)).save(cmd[-1], "JPEG")
            return subprocess.CompletedProcess(cmd, 0)

        with patch("photo.video.subprocess.run", run):
            source = video.make_poster(self.photo.get_full_url(), self.photo.id)

        self.assertTrue(os.path.exists(source))

    def test_empty_output_file_is_discarded(self):
        def run(cmd, **_kwargs):
            open(cmd[-1], "wb").close()
            return subprocess.CompletedProcess(cmd, 0)

        with patch("photo.video.subprocess.run", run):
            source = video.make_poster(self.photo.get_full_url(), self.photo.id)

        self.assertIsNone(source)
        self.assertFalse(os.path.exists(video.poster_path(self.photo.id)))

    def test_missing_ffmpeg_falls_back_to_the_file_path(self):
        with patch("photo.video.subprocess.run", side_effect=FileNotFoundError):
            source = self.photo.get_thumbnail_source()

        self.assertEqual(source, self.photo.get_full_url())

    def test_deleting_the_photo_removes_the_frame(self):
        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            frame = self.photo.get_thumbnail_source()

        with redirect_stdout(StringIO()):
            self.photo.delete()

        self.assertFalse(os.path.exists(frame))

    def test_removing_a_missing_frame_is_harmless(self):
        video.remove_poster(self.photo.id)  # nothing extracted yet

    def test_get_thumbnail_uses_the_frame(self):
        with (
            patch("photo.video.subprocess.run", FakeFfmpeg()),
            patch("photo.models.get_thumbnail") as sorl,
        ):
            sorl.return_value.url = "/thumb.jpg"
            url = self.photo.get_thumbnail(200)

        self.assertEqual(url, "/thumb.jpg")
        self.assertEqual(sorl.call_args.args[0], video.poster_path(self.photo.id))


class UploadVideoTests(PhotoRootTestCase):
    def upload(self, directory, **options):
        options.setdefault("defaulttags", "")
        with redirect_stdout(StringIO()):
            call_command("upload_album", directory=directory, stdout=StringIO(), **options)

    def test_scan_picks_up_videos_in_either_case(self):
        write_clip(self.photo_root, "2024", "clip.mp4")
        write_clip(self.photo_root, "2024", "LOUD.MP4")

        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            self.upload("/2024/")

        files = set(Photo.objects.filter(album__name="/2024/").values_list("file", flat=True))
        self.assertEqual(files, {"clip.mp4", "LOUD.MP4"})

    def test_scan_uses_container_creation_time_and_adds_date_tags(self):
        write_clip(self.photo_root, "2024", "clip.mp4")

        with patch("photo.video.subprocess.run", FakeFfmpeg(creation_time="2023-07-04T10:20:30Z")):
            self.upload("/2024/")

        photo = Photo.objects.get(file="clip.mp4")
        self.assertEqual(local(photo.date).date().isoformat(), "2023-07-04")
        tags = set(photo.tags.values_list("name", flat=True))
        self.assertEqual(tags, {"2023", "July"})

    def test_scan_falls_back_to_default_date_without_metadata(self):
        write_clip(self.photo_root, "2024", "clip.mp4")

        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            self.upload("/2024/", defaultdate=date(2022, 3, 5))

        photo = Photo.objects.get(file="clip.mp4")
        self.assertEqual(local(photo.date).date().isoformat(), "2022-03-05")


class VideoViewTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        media = tempfile.mkdtemp(prefix="photo-media-")
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        overrides = override_settings(MEDIA_ROOT=media)
        overrides.enable()
        self.addCleanup(overrides.disable)
        self.album = Album.objects.create(name="/2024/")
        self.path = write_clip(self.photo_root, "2024", "clip.mp4")
        self.photo = create_photo(self.album, "clip.mp4")
        self.size = len(CLIP_BYTES)
        self.url = reverse("photo:video", kwargs={"photo_id": self.photo.id})

    def body(self, response):
        return b"".join(response.streaming_content)

    def test_serves_the_whole_file(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "video/mp4")
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Length"], str(self.size))
        self.assertEqual(self.body(response), CLIP_BYTES)

    def test_range_request_returns_partial_content(self):
        response = self.client.get(self.url, headers={"Range": "bytes=10-19"})

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Range"], f"bytes 10-19/{self.size}")
        self.assertEqual(self.body(response), CLIP_BYTES[10:20])

    def test_open_ended_and_suffix_ranges(self):
        response = self.client.get(self.url, headers={"Range": "bytes=5-"})
        self.assertEqual(response["Content-Range"], f"bytes 5-{self.size - 1}/{self.size}")
        self.assertEqual(self.body(response), CLIP_BYTES[5:])

        response = self.client.get(self.url, headers={"Range": "bytes=-4"})
        self.assertEqual(self.body(response), CLIP_BYTES[-4:])

    def test_range_end_beyond_the_file_is_clamped(self):
        response = self.client.get(self.url, headers={"Range": f"bytes=0-{self.size * 10}"})

        self.assertEqual(response["Content-Range"], f"bytes 0-{self.size - 1}/{self.size}")

    def test_unsatisfiable_range_is_416(self):
        response = self.client.get(self.url, headers={"Range": f"bytes={self.size + 5}-"})

        self.assertEqual(response.status_code, 416)
        self.assertEqual(response["Content-Range"], f"bytes */{self.size}")

    def test_reversed_range_is_416(self):
        response = self.client.get(self.url, headers={"Range": "bytes=20-10"})

        self.assertEqual(response.status_code, 416)

    def test_malformed_range_is_ignored(self):
        for header in ("bytes=abc", "bytes=-", "items=1-2"):
            response = self.client.get(self.url, headers={"Range": header})
            self.assertEqual(response.status_code, 200, header)

    def test_stops_cleanly_if_the_file_shrinks_while_streaming(self):
        response = self.client.get(self.url)
        with open(self.path, "wb"):
            pass

        self.assertEqual(self.body(response), b"")

    def test_non_video_is_404(self):
        photo = create_photo(self.album, "a.jpg")

        response = self.client.get(reverse("photo:video", kwargs={"photo_id": photo.id}))

        self.assertEqual(response.status_code, 404)

    def test_missing_file_is_404(self):
        os.remove(self.path)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_view_returns_the_poster_frame_for_a_video(self):
        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            response = self.client.get(reverse("photo:view", kwargs={"photo_id": self.photo.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test_album_and_edit_pages_render_video_markup(self):
        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            response = self.client.get(reverse("photo:album", kwargs={"album_id": self.album.id}))
            self.assertContains(response, "video-badge")
            self.assertContains(response, self.url)

            response = self.client.get(reverse("photo:edit", kwargs={"photo_id": self.photo.id}))
            self.assertContains(response, "<video")


class VideoWithOtherCommandsTests(PhotoRootTestCase):
    def setUp(self):
        super().setUp()
        self.album = Album.objects.create(name="/2024/")
        write_clip(self.photo_root, "2024", "clip.mp4")
        self.photo = create_photo(self.album, "clip.mp4")

    def redate(self):
        with redirect_stdout(StringIO()) as out:
            call_command("clean_redate_photos", album=str(self.album.id))
        return out.getvalue()

    def test_redate_uses_video_metadata_and_does_not_crash(self):
        with patch("photo.video.subprocess.run", FakeFfmpeg(creation_time="2023-07-04T10:20:30Z")):
            self.redate()

        self.photo.refresh_from_db()
        self.assertEqual(local(self.photo.date).date().isoformat(), "2023-07-04")

    def test_redate_leaves_a_video_without_metadata_alone(self):
        before = self.photo.date

        with patch("photo.video.subprocess.run", FakeFfmpeg()):
            output = self.redate()

        self.photo.refresh_from_db()
        self.assertEqual(self.photo.date, before)
        self.assertIn("No creation date in video: clip.mp4", output)

    def test_rewrite_exif_skips_videos(self):
        with (
            patch("photo.lib.XMPFiles") as xmp,
            redirect_stdout(StringIO()),
        ):
            call_command("clean_rewrite_exif_data", album=str(self.album.id))

        xmp.assert_not_called()


@skipUnless(HAS_FFMPEG, "ffmpeg not installed")
class RealFfmpegTests(PhotoRootTestCase):
    """End to end with the real binaries, to catch drift from the faked command lines."""

    def test_real_clip_gets_a_date_and_a_frame(self):
        media = tempfile.mkdtemp(prefix="photo-media-")
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        path = os.path.join(self.photo_root, "2024", "clip.mp4")
        os.makedirs(os.path.dirname(path))
        subprocess.run(
            [
                *("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=64x48:d=1"),
                *("-metadata", "creation_time=2023-07-04T10:20:30Z", path),
            ],
            check=True,
        )

        with override_settings(MEDIA_ROOT=media):
            parsed = video.get_video_date(path)
            frame = video.make_poster(path, 1)

        self.assertEqual(parsed.date().isoformat(), "2023-07-04")
        with Image.open(frame) as im:
            self.assertEqual(im.format, "JPEG")
