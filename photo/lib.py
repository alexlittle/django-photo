from PIL import Image
from PIL.ExifTags import TAGS

import piexif

from django.conf import settings

def rewrite_exif(photo):
    
    photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
    if photo.title:
        desc = photo.title + " - " + photo.get_tags(", ")
    else:
        desc = photo.get_tags(", ")
    image = Image.open(photo_path)
    if image.format == "JPEG":
        piexif_dict = piexif.load(photo_path)
        piexif_dict['Exif'][piexif.ExifIFD.UserComment] = bytes(desc, 'utf-8') 
        piexif_dict['0th'][piexif.ImageIFD.ImageDescription] = bytes(desc, 'utf-8')
        piexif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = \
            photo.date.strftime('%Y:%m:%d %H:%M:%S')
        piexif_bytes = piexif.dump(piexif_dict)
        image.save(photo_path,
                   exif=piexif_bytes,
                   quality=100, 
                   optimization=True)
    else:
        print("Image is not a jpeg file")