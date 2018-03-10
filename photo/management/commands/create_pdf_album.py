
"""
Management command to create pdf album
"""
import os
import time 
import django.db.models

from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from photo.models import Photo, ThumbnailCache, Album

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER

class Command(BaseCommand):
    help = "Creates pdf album"


    def add_arguments(self, parser):        
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):
        try:
            album = Album.objects.get(id=options['album'])
        except Album.DoesNotExist:
            print "No Album Specified"
            return
        
        print "Creating album for... " + album.name
        
        doc = SimpleDocTemplate("/home/alex/temp/hello.pdf",pagesize=A4,
                        rightMargin=30,leftMargin=30,
                        topMargin=30,bottomMargin=30)
        
        photos = Photo.objects.filter(album=album).order_by('date')
        photo_page = []
        styles=getSampleStyleSheet()
        
        
        image = settings.MEDIA_ROOT + '..' + album.get_cover(album,700)
        im = Image(image)
        photo_page.append(im)
        
        styleCentered = ParagraphStyle(name="centeredStyle", alignment=TA_CENTER)
        
        photo_page.append(Spacer(1, 12))
        ptext = '<font size=40>Edward Robin Blythe Little</font>'
        photo_page.append(Paragraph(ptext, styleCentered))
        photo_page.append(Spacer(1, 50))
        ptext = '<font size=25>17 Dec 1937 - 23 Aug 2017</font>'
        photo_page.append(Paragraph(ptext, styleCentered))
        
        for photo in photos:
            #image = settings.PHOTO_ROOT + album.name + photo.file
            image = settings.MEDIA_ROOT + '..' + photo.get_thumbnail(photo,700)
            im = Image(image)
            photo_page.append(im)
            photo_page.append(Spacer(1, 12))
            if photo.title:
                ptext = '<font size=20>' + photo.title + '</font>'
                photo_page.append(Paragraph(ptext, styleCentered))
                photo_page.append(Spacer(1, 15))
            
            ptext = '<font size=12>' + photo.date.strftime('%B %Y')+ '</font>'
            photo_page.append(Paragraph(ptext, styleCentered))
            photo_page.append(Spacer(1, 12))
            
        doc.build(photo_page)
        