import os
from xml.sax.saxutils import escape

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import TA_CENTER, ParagraphStyle
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from photo.models import Album, Photo, Tag


def make_font_tag(size, text):
    return f"<font size={size}>{escape(str(text))}</font>"


def resolve_album_export(album_id):
    """Return (photos, filename, album) for an album export, or None if it doesn't exist."""
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        print("No Album Specified")
        return None

    photos = (
        Photo.objects.filter(album=album)
        .exclude(photoprops__name="exclude.album.export", photoprops__value="true")
        .order_by("date")
    )
    return photos, album.title or str(album.id), album


def resolve_tag_export(tag_id):
    """Return (photos, filename, tag) for a tag export, or None if it doesn't exist."""
    try:
        tag = Tag.objects.get(pk=tag_id)
    except Tag.DoesNotExist:
        print("No Tag Specified")
        return None

    photos = (
        Photo.objects.filter(phototag__tag_id=tag_id)
        .exclude(photoprops__name="exclude.album.export", photoprops__value="true")
        .order_by("date")
    )
    return photos, tag.name, tag


def build_output_path(filename):
    # A title or tag name might contain "/", which would otherwise escape the
    # albums directory when joined into a path below.
    safe_filename = str(filename).replace("/", "-")
    album_url = f"albums/{safe_filename}.pdf"
    album_filename = os.path.join(settings.PHOTO_ROOT, album_url)
    os.makedirs(os.path.join(settings.PHOTO_ROOT, "albums"), exist_ok=True)
    return album_filename


def build_cover_page(album_id, album, tag_id, tag, style_centered):
    photo_page = []

    if album_id and album.has_cover():
        cover_photo = album.get_cover()
        image = os.path.join(settings.MEDIA_ROOT, "..", cover_photo.get_thumbnail(700)[1:])
        photo_page.append(Image(image))

    if album_id and album.title:
        photo_page.append(Spacer(1, 12))
        photo_page.append(Paragraph(make_font_tag(40, album.title), style_centered))
        photo_page.append(Spacer(1, 50))
        if album.date_display:
            photo_page.append(Paragraph(make_font_tag(25, album.date_display), style_centered))

    if tag_id:
        photo_page.append(Spacer(1, 12))
        photo_page.append(Paragraph(make_font_tag(40, tag.name), style_centered))
        photo_page.append(Spacer(1, 50))

    return photo_page


def build_photo_pages(photos, style_centered):
    photo_page = []
    for photo in photos:
        print(photo)
        image = os.path.join(settings.MEDIA_ROOT, "..", photo.get_thumbnail(700)[1:])
        photo_page.append(Image(image))
        photo_page.append(Spacer(1, 12))
        if photo.title:
            ptext = make_font_tag(20, f"[id:{photo.id}] - {photo.title}")
            photo_page.append(Paragraph(ptext, style_centered))
            photo_page.append(Spacer(1, 15))

        ptext = make_font_tag(12, photo.date.strftime("%B %Y"))
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 12))

    return photo_page


def make(album_id=None, tag_id=None):
    photos = Photo.objects.none()
    filename = None
    album = None
    tag = None

    if album_id:
        resolved = resolve_album_export(album_id)
        if resolved is None:
            return None
        photos, filename, album = resolved

    if tag_id:
        resolved = resolve_tag_export(tag_id)
        if resolved is None:
            return None
        photos, filename, tag = resolved

    print(f"Creating album for... {filename}")

    album_filename = build_output_path(filename)

    doc = SimpleDocTemplate(
        album_filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    style_centered = ParagraphStyle(name="centeredStyle", alignment=TA_CENTER)
    photo_page = build_cover_page(album_id, album, tag_id, tag, style_centered)
    photo_page.extend(build_photo_pages(photos, style_centered))

    doc.build(photo_page)

    return album_filename
