from django import template

register = template.Library()


@register.filter(name='get_thumbnail')
def get_thumbnail(photo, max_size):
    return photo.get_thumbnail(max_size)


@register.filter(name='get_cover')
def get_cover(album, max_size):
    return album.get_cover(album, max_size)


@register.filter(name='is_photo_selected')
def is_photo_selected(photo, checked_list):
    if str(photo.id) in checked_list:
        return True
    else:
        return False
