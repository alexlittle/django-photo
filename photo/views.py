
import glob
import os
import pytz
import re


from PIL import Image
from PIL.ExifTags import TAGS

from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Max
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext_lazy as _

from haystack.query import SearchQuerySet

from photo.forms import ScanFolderForm, EditPhotoForm, SearchForm, \
    UpdateTagsForm
from photo.models import Album, Photo, PhotoTag, Tag


def home_view(request):
    albums = Album.objects.all().annotate(
        max_date=Max('photo__date')).order_by('-max_date')
    years = Tag.objects.filter(tagcategory__slug='date')

    paginator = Paginator(albums, 25)
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
    photos = Photo.objects.filter(album=album).order_by('date')

    if request.GET.get('view', '') == 'print':
        photos = photos.exclude(
            photoprops__name='exclude.album.export', photoprops__value='true')

    paginator = Paginator(photos, 200)
    
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
                   'page': photos})


def tag_slug_view(request, slug):
    tag = Tag.objects.get(slug=slug)
    photos = Photo.objects.filter(phototag__tag=tag).order_by('date')

    paginator = Paginator(photos, 25)
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
                   'page': photos})


def cloud_view(request):
    tags = Tag.objects.all().order_by('name')
    return render(request, 'photo/cloud.html',
                  {'title': _('Cloud'),
                   'tags': tags})


def map_view(request):
    tags = Tag.objects.filter(tagcategory__name='Place') \
        .exclude(tagprops__name='lat', tagprops__value='0') \
        .exclude(tagprops__name='map.display', tagprops__value='false') \
        .distinct()

    return render(request, 'photo/map.html',
                  {'title': _('Map'),
                   'tags': tags})


def cloud_category_view(request, category):
    tags = Tag.objects.filter(tagcategory__name=category).order_by('name')
    return render(request, 'photo/cloud_category.html',
                  {'title': _('Cloud'), 'tags': tags})


def search_view(request):
    search_query = request.GET.get('q', '')

    if search_query:
        search_results = SearchQuerySet().filter(content=search_query)
    else:
        search_results = []

    data = {}
    data['q'] = search_query
    form = SearchForm(initial=data)

    paginator = Paginator(search_results, 50)
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
    photos = Photo.objects.filter(
        photoprops__name='favourite', photoprops__value='true') \
        .order_by('-date')
    paginator = Paginator(photos, 25)
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

            return HttpResponseRedirect(reverse('photo_album',
                                                kwargs={'album_id': album.id}))
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
            tags = [x.strip() for x in new_tags.split(',')]
            for t in tags:
                tag, created = Tag.objects.get_or_create(name=t)
                photo_tag, created = PhotoTag.objects.get_or_create(
                    photo=photo, tag=tag)
            photo.title = form.cleaned_data.get("title")
            photo.date = form.cleaned_data.get("date")
            photo.save()
        return HttpResponseRedirect(reverse('photo_album',
                                            kwargs={'album_id':
                                                    photo.album.id}))

    else:
        tags = Tag.objects.filter(
            phototag__photo=photo).values_list('name', flat=True)
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


def photo_update_tags(request, album_id):

    album = Album.objects.get(id=album_id)
    photo_ids = request.GET.getlist('photo_id', [])

    print(photo_ids)

    if request.method == 'POST':
        form = UpdateTagsForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data.get("action")
            update_tags = form.cleaned_data.get("tags")
            date = form.cleaned_data.get("date")
            tags = [x.strip() for x in update_tags.split(',')]

            for t in tags:
                if t is not None:
                    tag, created = Tag.objects.get_or_create(name=t)

                    for p in photo_ids:
                        photo = Photo.objects.get(id=p)
                        if action == "delete":
                            PhotoTag.objects.filter(
                                photo__album=album, photo=photo, tag=tag) \
                                .delete()

                        if action == "add":
                            photo_tag, created = PhotoTag.objects \
                                .get_or_create(photo=photo, tag=tag)

            if action == "change_date":
                for p in photo_ids:
                    photo = Photo.objects.get(id=p)
                    photo.date = date
                    photo.save()
                    
            if action == 'change_album':
                new_album = Album.objects.get(pk=form.cleaned_data.get("album"))
                print(new_album.name)
                for p in photo_ids:
                    photo = Photo.objects.get(id=p)
                    try:
                        os.rename(os.path.join(settings.PHOTO_ROOT + photo.album.name, photo.file),
                                  os.path.join(settings.PHOTO_ROOT + new_album.name, photo.file))
                        photo.album = new_album
                        photo.save()
                    except OSError:
                        print("file could not be moved")
                    
                    

            return HttpResponseRedirect(reverse('photo_album',
                                                kwargs={'album_id': album_id}))
    else:
        form = UpdateTagsForm()

    return render(request, 'photo/update_tags.html',
                  {'form': form,
                   'title': _(u'Update Tags'), 'album': album})


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
    tags = [x.strip() for x in default_tags.split(',')]

    # find if dir is already in locations
    album, created = Album.objects.get_or_create(name=directory)

    # get all the image files from dir
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.gif', '*.bmp']

    for img_ext in image_extensions:
        image_files = glob.glob(settings.PHOTO_ROOT + directory + img_ext)
        for im in image_files:

            image_file_name = os.path.basename(im)
            print(image_file_name)
            # find if image exists
            photo, created = Photo.objects.get_or_create(
                album=album, file=image_file_name)

            # add all the tags
            for t in tags:
                tag, created = Tag.objects.get_or_create(name=t)
                photo_tag, created = PhotoTag.objects.get_or_create(
                    photo=photo, tag=tag)

            try:
                exif_tags, result = get_exif(im)
            except AttributeError:  # png files don't generally have exif data
                result = False
            if result:
                try:
                    exif_date = exif_tags['DateTimeOriginal']
                    naive = parse_datetime(re.sub(r'\:', r'-', exif_date, 2))
                    photo.date = pytz.timezone(
                        "Europe/London").localize(naive, is_dst=None)
                except KeyError:
                    if created:
                        photo.date = default_date
                except AttributeError:
                    if created:
                        photo.date = default_date
                except ValueError:
                    if created:
                        photo.date = default_date

            photo.save()
            # create thumbnails
            for size in settings.DEFAULT_THUMBNAIL_SIZES:
                photo.get_thumbnail(photo, size)
    return album
