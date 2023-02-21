import piexif
import re

from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings


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
