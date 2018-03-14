# oppia/local_settings.py

def modify(settings):
    
    settings['INSTALLED_APPS'] += ('photo','crispy_forms','haystack')
    settings['CRISPY_TEMPLATE_PACK'] = 'bootstrap3'
    settings['PHOTO_ROOT'] = '/home/alex/data/photos'
    settings['DEFAULT_THUMBNAIL_SIZES'] = [250]
    
    settings['HAYSTACK_CONNECTIONS'] = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'INCLUDE_SPELLING': True,
            #'URL': 'http://127.0.0.1:8983/solr'
            # ...or for multicore...
            'URL': 'http://127.0.0.1:8983/solr/photo/',
        }
    }                                
    settings['HAYSTACK_SIGNAL_PROCESSOR'] = 'haystack.signals.RealtimeSignalProcessor'
    
    settings['GEONAMES_USERNAME'] = 'alexlittle'
    
    settings['ALBUM_COVER_THUMBNAIL_SIZE'] = 150
    settings['PHOTO_DEFAULT_THUMBNAIL_SIZE'] = 250
    settings['PHOTO_DEFAULT_PDF_SIZE'] = 700
    
    # @todo - use these in map.html template
    settings['HOME_LAT'] = 62.60
    settings['HOME_LNG'] = 29.76
    

    