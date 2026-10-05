"""
Management command to find any videos that haven't been uploaded.

Same two passes as ``files_scan_photos`` (--files, --db), but only for video
files; photos are left to that command.
"""

from photo.management.commands.files_scan_photos import Command as ScanPhotosCommand
from photo.video import is_video


class Command(ScanPhotosCommand):
    help = "Checks for videos that aren't in the database"
    label = "videos"
    use_ignore_extensions = False

    def wants(self, filename):
        return is_video(filename)
