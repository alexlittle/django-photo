import piexif
import re

from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings

from photo.models import Tag, PhotoTag

def ignore_folder(dir): 
    for f in settings.IGNORE_FOLDERS:
        p = re.compile(f)
        if p.match(dir):
            return True
    return False


def ignore_file(filename):
    for ext in settings.IGNORE_EXTENSIONS:
        if filename.lower().endswith(ext):
            return True
    return False


def add_tags(photo, tags_str):
    tags = [x.strip() for x in tags_str.split(',')]
    for t in tags:
        if t.strip():
            tag, created = Tag.objects.get_or_create(name=t)
            photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)
    return created

   
def rewrite_exif(photo):
    
    photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
    
    if photo.title:
        desc = photo.title + " - " + photo.get_tags(", ")
    else:
        desc = photo.get_tags(", ")

    zeroth_ifd = {piexif.ImageIFD.Software: desc,
                piexif.ImageIFD.ImageDescription: desc,
                piexif.ImageIFD.ImageHistory: desc}
    exif_ifd = {piexif.ExifIFD.DateTimeOriginal: photo.date.strftime('%Y:%m:%d %H:%M:%S')}
               
    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd }
    exif_bytes = piexif.dump(exif_dict)
                
    with open(photo_path, 'r+b') as f:
        with Image.open(photo_path,'r') as image:
            if image.format == "JPEG":
                image.save(photo_path, "jpeg", quality=100, exif=exif_bytes)
            else:
                print("Image is not a jpeg file")
