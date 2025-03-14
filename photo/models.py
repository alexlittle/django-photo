import hashlib
import os
import piexif

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.db import models, connection
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from io import BytesIO

from PIL import Image


class CombinedSearchManager(models.Manager):
    def combined_search(self, query):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                   DISTINCT p.id
                FROM
                    photo_photo p
                INNER JOIN photo_phototag pt ON p.id = pt.photo_id
                INNER JOIN photo_tag t ON t.id = pt.tag_id
                INNER JOIN photo_album a ON a.id = p.album_id
                WHERE
                    MATCH(p.file, p.title) AGAINST(%s IN NATURAL LANGUAGE MODE)
                OR
                    MATCH (t.name, t.slug) AGAINST (%s IN NATURAL LANGUAGE MODE)
                OR
                    MATCH (a.name, a.title, a.date_display) AGAINST (%s IN NATURAL LANGUAGE MODE)

                ;
            """, [query, query, query])

            results = [{'id': row[0]} for row in cursor.fetchall()]
        return results

class CombinedSearch(models.Model):
    objects = CombinedSearchManager()


class Album (models.Model):
    name = models.TextField(blank=False, null=False)
    title = models.TextField(blank=True, null=True)
    date_display = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Album')
        verbose_name_plural = _('Albums')

    def has_cover(self):
        try:
            Photo.objects.get(album=self, album_cover=True)
        except Photo.DoesNotExist:
            return False
        except Photo.MultipleObjectsReturned:
            pass
        return True

    def has_multiple_covers(self):
        try:
            Photo.objects.get(album=self, album_cover=True)
        except Photo.DoesNotExist:
            return False
        except Photo.MultipleObjectsReturned:
            return True
        return False

    def get_count(self):
        return Photo.objects.filter(album=self).count()

    @staticmethod
    def get_cover(album, max_size):
        try:
            p = Photo.objects.get(album=album, album_cover=True)
        except Photo.DoesNotExist:
            try:
                p = Photo.objects.filter(album=album).earliest('date')
            except Photo.DoesNotExist:
                return None
        except Photo.MultipleObjectsReturned:
            p = Photo.objects.filter(album=album, album_cover=True).first()

        return p.get_thumbnail(max_size)


class TagCategory(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    slug = models.SlugField()
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tag Category')
        verbose_name_plural = _('Tag Categories')

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(TagCategory, self).save(*args, **kwargs)


class Tag (models.Model):
    name = models.TextField(blank=False, null=False)
    slug = models.SlugField()
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    tagcategory = models.ForeignKey(
        TagCategory, null=True, default=None, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)

    def get_prop(self, property):
        try:
            tag_prop = TagProps.objects.get(tag=self, name=property)
            return tag_prop.value
        except TagProps.DoesNotExist:
            return None

    def get_props(self):
        return TagProps.objects.filter(tag=self)

    def get_lat(self):
        return self.get_prop('lat')

    def get_lng(self):
        return self.get_prop('lng')

    def get_photo_count(self):
        return Photo.objects.filter(phototag__tag=self).count()


class Photo (models.Model):
    file = models.CharField(max_length=250, blank=False, null=False, unique=True)
    date = models.DateTimeField(default=timezone.now)
    title = models.TextField(blank=True, null=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    album_cover = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, through='PhotoTag', name='tags')
    md5hash = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.file

    class Meta:
        verbose_name = _('Photo')
        verbose_name_plural = _('Photos')

    def get_prop(self, property):
        try:
            photo_prop = PhotoProps.objects.get(photo=self, name=property)
            return photo_prop.value
        except PhotoProps.DoesNotExist:
            return None

    def set_prop(self, property, value):
        if self.get_prop(property) is None:
            pp = PhotoProps(photo=self, name=property, value=value)
            pp.save()
        else:
            pp = PhotoProps.objects.get(photo=self, name=property)
            pp.value = value
            pp.save()
        return True

    def get_props(self):
        return PhotoProps.objects.filter(photo=self)

    def get_tags(self, separator):
        tags = Tag.objects.filter(
            phototag__photo=self).values_list('name', flat=True)
        return separator.join(tags)

    def get_full_url(self):
        return settings.PHOTO_ROOT + self.album.name + self.file

    def get_thumbnail(self, max_size):
        try:
            thumb = ThumbnailCache.objects.filter(photo=self, size=max_size)[:1].get()
        except ThumbnailCache.DoesNotExist:
            try:
                image = settings.PHOTO_ROOT + self.album.name + self.file
                im = Image.open(image)
                # preserve exif data
                try:
                    exif_dict = piexif.load(im.info["exif"])
                    exif_bytes = piexif.dump(exif_dict)
                except (KeyError, ValueError):
                    exif_bytes = None
                    print("No exif data for %s" % image)

                if self.file.lower().endswith(".png"):
                    format = "PNG"
                    content_type = "image/png"
                else:
                    format = "JPEG"
                    content_type = "image/jpeg"

                im.thumbnail((int(max_size), int(max_size)), Image.LANCZOS)
                buffer = BytesIO()
                if exif_bytes:
                    im.save(fp=buffer, format=format, dpi=(600, 600), exif=exif_bytes)
                else:
                    im.save(fp=buffer, format=format, dpi=(600, 600))
                pillow_image = ContentFile(buffer.getvalue())
                file_name = hashlib.md5(buffer.getvalue()).hexdigest()
                thumb = ThumbnailCache(size=max_size,
                                       photo=self,
                                       image=InMemoryUploadedFile(
                                            pillow_image, None, file_name,
                                            content_type, pillow_image.tell,
                                            None)
                                       )
                thumb.save()
                print("Thumbnail created (%d) - %s" % (max_size, thumb.image.name))
            except (TypeError, IOError) as ioe:
                print(self.id)
                print(ioe)
                return None

        return thumb.image.url

    def get_face_count(self):
        count = self.get_prop('face_count')
        return count

@receiver(post_delete, sender=Photo)
def photo_delete_file(sender, instance, **kwargs):
    file_to_delete = settings.PHOTO_ROOT + instance.album.name + instance.file
    print("deleting ...." + file_to_delete)
    try:
        os.remove(file_to_delete)
    except OSError:
        print("File not removed")


class PhotoProps(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    value = models.TextField(blank=False, null=False)

    class Meta:
        verbose_name = _('Photo property')
        verbose_name_plural = _('Photo properties')


class PhotoTag(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag,  on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Photo Tag')
        verbose_name_plural = _('Photo Tags')


class TagProps(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        unique_together = ('tag', 'name')
        verbose_name = _('Tag property')
        verbose_name_plural = _('Tag properties')


def image_file_name(instance, filename):
    basename, ext = os.path.splitext(filename)
    return os.path.join('cache', filename[0:2], filename[2:4], filename + ext.lower())


class ThumbnailCache(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    size = models.IntegerField(blank=False, null=False)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=image_file_name, blank=True, null=True)

    class Meta:
        verbose_name = _('Thumbnail Cache')
        verbose_name_plural = _('Thumbnail Caches')


@receiver(post_delete, sender=ThumbnailCache)
def thumbnail_delete_file(sender, instance, **kwargs):
    file_to_delete = settings.MEDIA_ROOT + instance.image.name
    print("deleting ...." + file_to_delete)
    try:
        os.remove(file_to_delete)
    except OSError:
        print("File not removed")
