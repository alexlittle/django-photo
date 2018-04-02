
import os

from django.conf import settings

from photo.models import Photo, ThumbnailCache, Album

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER


def make(album_id):
    try:
        album = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        print "No Album Specified"
        return
    
    print "Creating album for... " + album.name
    
    if album.title:
        filename = album.title
    else:
        filename = str(album.id)
    
    album_url = 'albums/' +  filename + ".pdf"
    album_filename = os.path.join(settings.PHOTO_ROOT, album_url) 
        
    doc = SimpleDocTemplate(album_filename,pagesize=A4,
                    rightMargin=30,leftMargin=30,
                    topMargin=30,bottomMargin=30)
    
    photos = Photo.objects.filter(album=album).exclude(photoprops__name='exclude.album.export', photoprops__value='true').order_by('date')
    photo_page = []
    styles=getSampleStyleSheet()
    styleCentered = ParagraphStyle(name="centeredStyle", alignment=TA_CENTER)
    
    if album.has_cover():
        image = settings.MEDIA_ROOT + '..' + album.get_cover(album,700)
        im = Image(image)
        photo_page.append(im)
    
    if album.title:
        photo_page.append(Spacer(1, 12))
        ptext = '<font size=40>' + album.title + '</font>'
        photo_page.append(Paragraph(ptext, styleCentered))
        photo_page.append(Spacer(1, 50))
        if album.date_display:
            ptext = '<font size=25>' + album.date_display + '</font>'
            photo_page.append(Paragraph(ptext, styleCentered))
    
    for photo in photos:
        #image = settings.PHOTO_ROOT + album.name + photo.file
        image = settings.MEDIA_ROOT + '..' + photo.get_thumbnail(photo,700)
        im = Image(image)
        photo_page.append(im)
        photo_page.append(Spacer(1, 12))
        if photo.title:
            ptext = '<font size=20>[id:{0}] - {1}</font>'.format(photo.id, photo.title)
            photo_page.append(Paragraph(ptext, styleCentered))
            photo_page.append(Spacer(1, 15))
        
        ptext = '<font size=12>' + photo.date.strftime('%B %Y')+ '</font>'
        photo_page.append(Paragraph(ptext, styleCentered))
        photo_page.append(Spacer(1, 12))
        
    doc.build(photo_page)
    
    return album_filename

