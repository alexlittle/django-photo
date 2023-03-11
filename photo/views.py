
import glob
import os
import pytz
import re
import datetime


from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Max, Count
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from haystack.query import SearchQuerySet

from photo.forms import ScanFolderForm, EditPhotoForm, SearchForm, UpdateTagsForm
from photo.lib import rewrite_exif, add_tags
from photo.models import Album, Photo, PhotoTag, Tag, TagCategory


def home_view(request):
    albums = Album.objects.all().annotate(max_date=Max('photo__date')).order_by('-max_date')
    years = Tag.objects.filter(tagcategory__slug='date')

    paginator = Paginator(albums, settings.ALBUMS_PER_PAGE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        albums = paginator.page(page)
    except (EmptyPage, InvalidPage):
        albums = paginator.page(paginator.num_pages)

    return render(request, 'photo/home.html',
                  {'page': albums,
                   'years': years,
                   'total_albums': paginator.count, })


def album_view(request, album_id):
    album = Album.objects.get(pk=album_id)
    photos = Photo.objects.filter(album=album).order_by('date','file')
    photos_checked = request.GET.getlist('photo_id', [])

    if request.GET.get('view', '') == 'print':
        photos = photos.exclude(photoprops__name='exclude.album.export', photoprops__value='true')

    photo_count = photos.count()
    
    paginator = Paginator(photos, settings.PHOTOS_PER_PAGE)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        photos = paginator.page(page)
    except (EmptyPage, InvalidPage):
        photos = paginator.page(paginator.num_pages)
        
    return render(request, 'photo/album.html',
                  {'album': album,
                   'page': photos,
                   'photo_count': photo_count,
                   'photos_checked': photos_checked })


def tag_slug_view(request, slug):
    tag = Tag.objects.get(slug=slug)
    photos = Photo.objects.filter(phototag__tag=tag).order_by('date')
    photos_checked = request.GET.getlist('photo_id', [])

    paginator = Paginator(photos, settings.PHOTOS_PER_PAGE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        photos = paginator.page(page)
    except (EmptyPage, InvalidPage):
        photos = paginator.page(paginator.num_pages)

    return render(request, 'photo/tag.html',
                  {'title': tag.name,
                   'page': photos,
                   'photos_checked': photos_checked })


def cloud_view(request):
    tags = Tag.objects.all().order_by('name')
    categories = TagCategory.objects.all().order_by('name')
    return render(request, 'photo/cloud.html',
                  {'title': _('Cloud'),
                   'tags': tags,
                   'categories': categories})


def map_view(request):
    tags = Tag.objects.filter(tagcategory__name='Location') \
        .exclude(tagprops__name='lat', tagprops__value='0') \
        .exclude(tagprops__name='map.display', tagprops__value='false') \
        .distinct()

    return render(request, 'photo/map.html',
                  {'title': _('Map'),
                   'tags': tags})


def cloud_category_view(request, category):
    tags = Tag.objects.filter(tagcategory__name=category).values('id', 'name', 'slug').annotate(count=Count('phototag')).order_by('name')
    return render(request, 'photo/cloud_category.html', {'title': _('Cloud'), 'tags': tags})


def search_view(request):
    search_query = request.GET.get('q', '')

    if search_query:
        search_results = SearchQuerySet().filter(content=search_query)
    else:
        search_results = []

    data = {}
    data['q'] = search_query
    form = SearchForm(initial=data)

    paginator = Paginator(search_results, settings.PHOTOS_PER_PAGE)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        results = paginator.page(page)
    except (EmptyPage, InvalidPage):
        results = paginator.page(paginator.num_pages)

    return render(request, 'photo/search.html', {
        'form': form,
        'query': search_query,
        'page': results,
        'total_results': paginator.count,
    })


def photo_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    image = settings.PHOTO_ROOT + photo.album.name + photo.file
    im = Image.open(image)
    response = HttpResponse(content_type="image/jpg")
    im.save(response, "JPEG")
    return response


def photo_favourites_view(request):
    photos = Photo.objects.filter(photoprops__name='favourite', photoprops__value='true').order_by('-date')
    paginator = Paginator(photos, settings.PHOTOS_PER_PAGE)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        photos_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        photos_page = paginator.page(paginator.num_pages)

    return render(request, 'photo/favourites.html',
                  {'page': photos_page})

    
def scan_folder(request):

    if request.method == 'POST':
        form = ScanFolderForm(request.POST)
        if form.is_valid():
            directory = form.cleaned_data.get("directory")
            if not directory.endswith('/'):
                directory = directory + '/'
            default_tags = form.cleaned_data.get("default_tags")
            default_date = form.cleaned_data.get("default_date")
            album = upload_album(directory, default_tags, default_date)

            return HttpResponseRedirect(reverse('photo_album',kwargs={'album_id': album.id}))
    else:
        data = {}
        data['default_date'] = timezone.now()
        data['directory'] = '/' + str(timezone.now().year) + '/'
        data['default_tags'] = ''
        form = ScanFolderForm(initial=data)

    return render(request, 'photo/scan.html', {'form': form,
                                               'title': _(u'Scan Folder')})


def photo_edit_view(request, photo_id):

    photo = Photo.objects.get(pk=photo_id)

    if request.method == 'POST':
        form = EditPhotoForm(request.POST)
        if form.is_valid():

            # delete any existing tags
            PhotoTag.objects.filter(photo=photo).delete()

            new_tags = form.cleaned_data.get("tags")
            add_tags(photo, new_tags)
            photo.title = form.cleaned_data.get("title")
            photo.date = form.cleaned_data.get("date").replace(hour=photo.date.hour, minute=photo.date.minute)
            photo.save()
            rewrite_exif(photo)
        return HttpResponseRedirect(reverse('photo_album',
                                            kwargs={'album_id':
                                                    photo.album.id}))

    else:
        tags = Tag.objects.filter(phototag__photo=photo).values_list('name', flat=True)
        data = {}
        data['tags'] = ", ".join(tags)
        data['title'] = photo.title
        data['date'] = photo.date
        form = EditPhotoForm(initial=data)

    return render(request, 'photo/edit.html', {'form': form,
                                               'title': _(u'Edit Photo'),
                                               'photo': photo})


def photo_set_cover(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    photos = Photo.objects.filter(album=photo.album, album_cover=True)
    for p in photos:
        p.album_cover = False
        p.save()

    photo.album_cover = True
    photo.save()

    return redirect('photo_album', album_id=photo.album.id)


def photo_star_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    photo.set_prop('favourite', 'true')
    return redirect('photo_album', album_id=photo.album.id)


def photo_unstar_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    photo.set_prop('favourite', 'false')
    return redirect('photo_album', album_id=photo.album.id)


def photo_update_tags(request):

    photo_ids = request.GET.getlist('photo_id', [])
    next = request.GET.get("next")

    if request.method == 'POST':
        form = UpdateTagsForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data.get("action")
            update_tags = form.cleaned_data.get("tags")
            date = form.cleaned_data.get("date")
            next = form.cleaned_data.get("next")
            tags = [x.strip() for x in update_tags.split(',')]

            for t in tags:
                if t.strip():
                    tag, created = Tag.objects.get_or_create(name=t)

                    for p in photo_ids:
                        try:
                            photo = Photo.objects.get(id=p)
                            if action == "delete":
                                PhotoTag.objects.filter(photo=photo, tag=tag).delete()
    
                            if action == "add":
                                photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)
                                rewrite_exif(photo)
                        except Photo.DoesNotExist:
                            pass

            if action == "change_date":
                for p in photo_ids:
                    photo = Photo.objects.get(id=p)
                    photo.date = date
                    photo.save()
                    rewrite_exif(photo)
                    
            if action == 'change_album':
                new_album = Album.objects.get(pk=form.cleaned_data.get("album"))
                for p in photo_ids:
                    photo = Photo.objects.get(id=p)
                    os.rename(os.path.join(settings.PHOTO_ROOT + photo.album.name, photo.file),
                              os.path.join(settings.PHOTO_ROOT + new_album.name, photo.file))
                    photo.album = new_album
                    photo.save()
            url_params = '&'.join(['photo_id={}'.format(x) for x in photo_ids])
            return HttpResponseRedirect(next + "?" + url_params)
    else:
        form = UpdateTagsForm(initial={'next': next})

    return render(request, 'photo/update_tags.html',
                  {'form': form,
                   'title': _(u'Update Tags')})


def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value
        return ret, True
    else:
        return None, False


def upload_album(directory, default_tags, default_date):

    # find if dir is already in locations
    album, created = Album.objects.get_or_create(name=directory)

    # get all the image files from dir
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.gif', '*.bmp', '*.JPG', '*.JPEG']

    for img_ext in image_extensions:
        image_files = glob.glob(settings.PHOTO_ROOT + directory + img_ext)
        for im in image_files:

            image_file_name = os.path.basename(im)
            print(image_file_name)
            # find if image exists
            photo, created = Photo.objects.get_or_create(album=album, file=image_file_name)

            # add all the tags
            add_tags(photo, default_tags)

            try:
                exif_tags, result = get_exif(im)
            except AttributeError:  # png files don't generally have exif data
                result = False
            if result:
                try:
                    exif_date = exif_tags['DateTimeOriginal']
                    naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2))
                    
                    photo.date = pytz.timezone("Europe/London").localize(naive, is_dst=None)

                    # add year and month tags   
                    year = photo.date.year
                    tag, created = Tag.objects.get_or_create(name=year)
                    photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)
                    
                    month = photo.date.strftime("%B")
                    tag, created = Tag.objects.get_or_create(name=month)
                    photo_tag, created = PhotoTag.objects.get_or_create(photo=photo, tag=tag)

                except (KeyError, AttributeError, ValueError):
                    if created:
                        photo.date = default_date

            photo.save()

            # create thumbnails
            for size in settings.DEFAULT_THUMBNAIL_SIZES:
                photo.get_thumbnail(size)
    return album

def album_exif(request, album_id):
    album = Album.objects.get(id=album_id)
    photos = Photo.objects.filter(album=album)
    for photo in photos:
        rewrite_exif(photo)
    return redirect('photo_album', album_id=album_id)
