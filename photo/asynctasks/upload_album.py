import os
import glob
import pytz
import re
# Celery
from celery import shared_task
# Celery-progress
from celery_progress.backend import ProgressRecorder

from django.conf import settings
from django.utils.dateparse import parse_datetime

from photo.models import Album, Photo, Tag, PhotoTag
from photo.lib import get_exif, add_tags

# Celery Task
@shared_task(bind=True)
def UploadAlbum(self, directory, default_tags, default_date):
	print('Task started')

	progress_recorder = ProgressRecorder(self)
	album, created = Album.objects.get_or_create(name=directory)

	print('Start')

	for img_ext in settings.IMAGE_EXTENSIONS:
		image_files = glob.glob(settings.PHOTO_ROOT + directory + img_ext)
		for idx, im in enumerate(image_files):
			image_file_name = os.path.basename(im)
			# find if image exists
			photo, created = Photo.objects.get_or_create(album=album, file=image_file_name)

			# add all the tags
			add_tags(photo, default_tags)

			try:
				exif_tags, result = get_exif(im)
			except AttributeError:  # png files don't generally have exif data
				result = False
			if result:
				try:
					exif_date = exif_tags['DateTimeOriginal']
					naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2))

					photo.date = pytz.timezone("Europe/London").localize(naive, is_dst=None)

					# add year and month tags
					year = photo.date.year
					tag, created = Tag.objects.get_or_create(name=year)
					photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)

					month = photo.date.strftime("%B")
					tag, created = Tag.objects.get_or_create(name=month)
					photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)

				except (KeyError, AttributeError, ValueError):
					if created:
						photo.date = default_date

			photo.save()

			# create thumbnails
			for size in settings.DEFAULT_THUMBNAIL_SIZES:
				photo.get_thumbnail(size)
			progress_recorder.set_progress(idx + 1, len(image_files), description="Processing album")
	return album.id