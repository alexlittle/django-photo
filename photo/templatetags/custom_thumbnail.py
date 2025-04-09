from django import template

register = template.Library()


@register.filter(name='is_photo_selected')
def is_photo_selected(photo, checked_list):
    if str(photo.id) in checked_list:
        return True
    else:
        return False
