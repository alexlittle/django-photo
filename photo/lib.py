import re
import os

from PIL import Image
from PIL.ExifTags import TAGS
from django.conf import settings
from libxmp import XMPFiles, XMPMeta, consts

from photo.models import Tag, PhotoTag


def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value
        return ret, True
    else:
        return None, False


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
    created = False
    for t in tags:
        if t.strip():
            tag, created = Tag.objects.get_or_create(name=t)
            photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)
    return created


def rename_photo_file(photo):
    current_full_path = settings.PHOTO_ROOT + photo.album.name + photo.file

    new_name = photo.file.replace(".", "-" + str(photo.id) + ".", 1)
    new_full_path = settings.PHOTO_ROOT + photo.album.name + new_name

    # rename photo file
    try:
        os.rename(current_full_path, new_full_path)
        # update photo object
        photo.file = new_name
        photo.save()
    except FileNotFoundError:
        print("File not found: %s" % photo.file)

    return True

def add_or_update_xmp_metadata(photo): #image_path, namespace_uri, property_name, property_value):
    """Adds or updates an XMP property in an image file.

    Args:
        image_path (str): Path to the image file.
        namespace_uri (str): The URI of the XMP namespace (e.g., consts.XMP_NS_DC for Dublin Core).
        property_name (str): The name of the property to add or update (e.g., 'subject').
        property_value (str or list): The value of the property. Use a list for array properties.
    """

    photo_path = settings.PHOTO_ROOT + photo.album.name + photo.file
    namespace_uri = consts.XMP_NS_DC
    property_name = 'subject'

    if photo.title:
        desc = photo.title + " - " + photo.get_tags(", ")
    else:
        desc = photo.get_tags(", ")

    # get location if exists
    lat, lng = photo.get_location()
    if lat != 0 and lng != 0:
        desc = f"({lat},{lng}), " + desc

    xmpfile = None
    try:
        xmpfile = XMPFiles(file_path=photo_path, open_forupdate=True)
        xmp = xmpfile.get_xmp()
        if xmp is None:
            xmp = XMPMeta()

        xmp.delete_property(namespace_uri, property_name)

        xmp.append_array_item(
            namespace_uri,
            property_name,
            desc,
            {'prop_array_is_unordered': True, 'prop_value_is_array': True}
        )

        if xmpfile.can_put_xmp(xmp):
            xmpfile.put_xmp(xmp)
        else:
            print(f"Could not write XMP to {photo_path}")

    except FileNotFoundError:
        print(f"Error: Image not found at {photo_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if xmpfile:
            xmpfile.close_file()
