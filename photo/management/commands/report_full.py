
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ""


    def handle(self, *args, **options):
        
        # deep structure
        call_command('files_deep_structure', count=2)
        
        # Missing albums (not in db but on disk)
        call_command('files_scan_albums')
        
        # Missing photos (not in db but on disk)
        
        # Missing photos (in db but not disk)
        
        # Non image files on disk
        
        # Uncategorised tags
        
        # Album cover issues
        call_command('integrity_album_covers')
        
        # Photos with only 1 tag
        
        # Small albums
        
         
        pass