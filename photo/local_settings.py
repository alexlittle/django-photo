# oppia/local_settings.py

def modify(settings):
    
    settings['INSTALLED_APPS'] += ('photo','crispy_forms')
    settings['CRISPY_TEMPLATE_PACK'] = 'bootstrap3'
    settings['PHOTO_ROOT'] = '/home/alex/data'
    

    