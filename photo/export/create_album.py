import os

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import TA_CENTER, ParagraphStyle
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from photo.models import Album, Photo, Tag


def make_font_tag(size, text):
    return f"<font size={size}>{text}</font>"


def make(album_id=None, tag_id=None):
    photos = Photo.objects.none()
    filename = None

    if album_id:
        try:
            album = Album.objects.get(id=album_id)
            photos = (
                Photo.objects.filter(album=album)
                .exclude(photoprops__name="exclude.album.export", photoprops__value="true")
                .order_by("date")
            )
            filename = album.title or str(album.id)
        except Album.DoesNotExist:
            print("No Album Specified")

    if tag_id:
        try:
            photos = (
                Photo.objects.filter(phototag__tag_id=tag_id)
                .exclude(photoprops__name="exclude.album.export", photoprops__value="true")
                .order_by("date")
            )
            tag = Tag.objects.get(pk=tag_id)
            filename = tag.name
        except Tag.DoesNotExist:
            print("No Tag Specified")

    print(f"Creating album for... {filename}")

    album_url = f"albums/{filename}.pdf"
    album_filename = os.path.join(settings.PHOTO_ROOT, album_url)

    doc = SimpleDocTemplate(
        album_filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    photo_page = []
    style_centered = ParagraphStyle(name="centeredStyle", alignment=TA_CENTER)

    if album_id and album.has_cover():
        cover_photo = album.get_cover()
        image = os.path.join(settings.MEDIA_ROOT, "..", cover_photo.get_thumbnail(700)[1:])
        im = Image(image)
        photo_page.append(im)

    if album_id and album.title:
        photo_page.append(Spacer(1, 12))
        ptext = make_font_tag(40, album.title)
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 50))
        if album.date_display:
            ptext = make_font_tag(25, album.date_display)
            photo_page.append(Paragraph(ptext, style_centered))

    if tag_id:
        photo_page.append(Spacer(1, 12))
        ptext = make_font_tag(40, tag.name)
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 50))

    for photo in photos:
        print(photo)
        image = os.path.join(settings.MEDIA_ROOT, "..", photo.get_thumbnail(700)[1:])
        im = Image(image)
        photo_page.append(im)
        photo_page.append(Spacer(1, 12))
        if photo.title:
            ptext = make_font_tag(20, f"[id:{photo.id}] - {photo.title}")
            photo_page.append(Paragraph(ptext, style_centered))
            photo_page.append(Spacer(1, 15))

        ptext = make_font_tag(12, photo.date.strftime("%B %Y"))
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 12))

    doc.build(photo_page)

    return album_filename
