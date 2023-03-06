
import os

from django.conf import settings

from photo.models import Photo, Album, Tag

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle, TA_CENTER


def make(album_id=None, tag_id=None):
    photos = None
    filename = None
    
    try:
        album = Album.objects.get(id=album_id)
        photos = Photo.objects.filter(album=album) \
            .exclude(photoprops__name='exclude.album.export',
                     photoprops__value='true') \
            .order_by('date')
        if album.title:
            filename = album.title
        else:
            filename = str(album.id)
    except Album.DoesNotExist:
        print("No Album Specified")
        
    try:
        photos = Photo.objects.filter(phototag__tag_id=tag_id) \
            .exclude(photoprops__name='exclude.album.export',
                     photoprops__value='true') \
            .order_by('date')
        tag = Tag.objects.get(pk=tag_id)
        filename = tag.name
    except Tag.DoesNotExist:
        print("No Tag Specified")

    print("Creating album for... " + filename)


    album_url = 'albums/' + filename + ".pdf"
    album_filename = os.path.join(settings.PHOTO_ROOT, album_url)

    doc = SimpleDocTemplate(album_filename, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    photo_page = []
    style_centered = ParagraphStyle(name="centeredStyle", alignment=TA_CENTER)

    if album_id and album.has_cover():
        image = os.path.join(settings.MEDIA_ROOT,
                             '..',
                             album.get_cover(album, 700)[1:])
        im = Image(image)
        photo_page.append(im)

    if album_id and album.title:
        photo_page.append(Spacer(1, 12))
        ptext = '<font size=40>' + album.title + '</font>'
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 50))
        if album.date_display:
            ptext = '<font size=25>' + album.date_display + '</font>'
            photo_page.append(Paragraph(ptext, style_centered))
            
    if tag_id:
        photo_page.append(Spacer(1, 12))
        ptext = '<font size=40>' + tag.name + '</font>'
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 50))

    for photo in photos:
        print(photo)
        image = os.path.join(settings.MEDIA_ROOT, '..', photo.get_thumbnail(700)[1:])
        im = Image(image)
        photo_page.append(im)
        photo_page.append(Spacer(1, 12))
        if photo.title:
            ptext = '<font size=20>[id:{0}] - {1}</font>' \
                .format(photo.id, photo.title)
            photo_page.append(Paragraph(ptext, style_centered))
            photo_page.append(Spacer(1, 15))

        ptext = '<font size=12>' + photo.date.strftime('%B %Y') + '</font>'
        photo_page.append(Paragraph(ptext, style_centered))
        photo_page.append(Spacer(1, 12))

    doc.build(photo_page)

    return album_filename
