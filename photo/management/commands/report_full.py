
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
        call_command('files_scan_photos', files=True)
        
        # Missing photos (in db but not disk)
        call_command('files_scan_photos', db=True)
        
        # Non image files on disk
        
        # Uncategorised tags
        #call_command('integrity_uncategorised_tags')
        
        # Album cover issues
        #call_command('integrity_album_covers')
        
        # Album without titles
        #call_command('integrity_albums_no_title')
        
        # Photos with only 1 tag
        #call_command('integrity_only_one_tag')
        
        # Small albums
        #call_command('integrity_small_albums', count=9)
        
        # remove empty albums
        #call_command('integrity_remove_empty_albums')
        
        # remove unused tags
        #call_command('integrity_remove_empty_albums') 
