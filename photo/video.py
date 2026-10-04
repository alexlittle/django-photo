"""Helpers for video files: detection, creation date and poster frames (via ffmpeg/ffprobe)."""

import contextlib
import os
import subprocess

from django.conf import settings
from django.utils.dateparse import parse_datetime

FFMPEG_TIMEOUT = 60


def is_video(filename):
    return filename.lower().endswith(tuple(settings.VIDEO_EXTENSIONS))


def get_video_date(path):
    """Creation time from the container metadata as an aware datetime, or None."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format_tags=creation_time",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT,
            check=False,
        )
    except OSError, subprocess.SubprocessError:
        return None

    value = result.stdout.strip()
    if not value:
        return None
    try:
        parsed = parse_datetime(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed is None or parsed.tzinfo is None or parsed.year < 1990:
        return None  # some cameras write 1970/1904 epoch placeholders
    return parsed


def poster_path(photo_id):
    return os.path.join(settings.MEDIA_ROOT, "video_frames", f"{photo_id}.jpg")


def make_poster(video_path, photo_id):
    """Extract a frame from the video as a JPEG; returns its path, or None on failure."""
    out = poster_path(photo_id)
    if os.path.exists(out):
        return out

    os.makedirs(os.path.dirname(out), exist_ok=True)
    # try 1s in first; very short clips have no frame there, so retry from the start
    for seek in ("1", "0"):
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    seek,
                    "-i",
                    video_path,
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    out,
                ],
                capture_output=True,
                timeout=FFMPEG_TIMEOUT,
                check=False,
            )
        except OSError, subprocess.SubprocessError:
            return None
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        if os.path.exists(out):
            os.remove(out)
    return None


def remove_poster(photo_id):
    with contextlib.suppress(OSError):
        os.remove(poster_path(photo_id))
