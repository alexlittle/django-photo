
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
        
        photos = Photo.objects.filter(album=album)
        photo_page = []
        
        for photo in photos:
            #image = settings.PHOTO_ROOT + album.name + photo.file
            image = settings.MEDIA_ROOT + '..' + photo.get_thumbnail(photo,1000)
            im = Image(image)
            photo_page.append(im)
            
        doc.build(photo_page)
        