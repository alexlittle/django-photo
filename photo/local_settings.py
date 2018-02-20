# oppia/local_settings.py

def modify(settings):
    
    settings['INSTALLED_APPS'] += ('photo','crispy_forms','haystack')
    settings['CRISPY_TEMPLATE_PACK'] = 'bootstrap3'
    settings['PHOTO_ROOT'] = '/home/alex/data'
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
    

    