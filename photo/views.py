
import os
import json

from io import StringIO

from PIL import Image, ImageDraw



from django.conf import settings
from django.core import management
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Max, Count
from django.shortcuts import render, redirect
from django.utils import timezone


from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, ListView


from photo.asynctasks.face_detection import FaceDetection
from photo.forms import ScanFolderForm, EditPhotoForm, SearchForm, UpdateTagsForm
from photo.lib import rewrite_exif, add_tags
from photo.models import Album, Photo, PhotoTag, Tag, TagCategory, CombinedSearch

# Celery Task
from photo.tasks import UploadAlbum


class HomeView(ListView):

    template_name = 'photo/home.html'
    paginate_by = settings.ALBUMS_PER_PAGE
    context_object_name = 'albums'

    def get_queryset(self):
        return Album.objects.all().annotate(max_date=Max('photo__date')).order_by('-max_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['years'] = Tag.objects.filter(tagcategory__slug='date')
        return context

class AlbumView(TemplateView):

    def get(self, request, album_id):
        album = Album.objects.get(pk=album_id)
        photos = Photo.objects.filter(album=album).order_by('date', 'file')
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

        context = {'album': album,
                       'page': photos,
                       'photo_count': photo_count,
                       'photos_checked': photos_checked,
                     }
        if request.GET.get('detect', None) is not None:
            # Create Task
            upload_task = FaceDetection.delay(album_id)
            # Get ID
            context['task_id'] = upload_task.task_id

        return render(request, 'photo/album.html',
                      context)


def tag_slug_view(request, slug):
    slug_list = slug.split('+')
    tags = Tag.objects.filter(slug__in=slug_list)
    photos = Photo.objects.filter(phototag__tag__slug__in=slug_list) \
                .annotate(count=Count('id')) \
                .filter(count=len(slug_list)) \
                .order_by('date')
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
                  {'tags': tags,
                   'page': photos,
                   'photos_checked': photos_checked})


def cloud_view(request):
    tags = Tag.objects.all().order_by('name')
    categories = TagCategory.objects.all().order_by('name')
    return render(request, 'photo/cloud.html',
                  {'title': _('Cloud'),
                   'tags': tags,
                   'categories': categories})


def map_view(request):
    tags = Tag.objects.filter(tagcategory__name='Location', tagprops__name='source', tagprops__value='me') \
        .exclude(tagprops__name='lat', tagprops__value='0') \
        .exclude(tagprops__name='map.display', tagprops__value='false') \
        .distinct()

    return render(request, 'photo/map.html',
                  {'title': _('Map'),
                   'tags': tags})


def cloud_category_view(request, category):
    tags = Tag.objects.filter(tagcategory__name=category) \
        .values('id', 'name', 'slug') \
        .annotate(count=Count('phototag')).order_by('name')
    return render(request, 'photo/cloud_category.html', {'title': _('Cloud'), 'tags': tags})


def search_view(request):
    search_query = request.GET.get('q', '')

    if search_query:
        search_id_results = CombinedSearch.objects.combined_search(search_query)
        search_ids = [result['id'] for result in search_id_results]
    else:
        search_ids = []

    search_results = Photo.objects.filter(pk__in=search_ids)

    data = {'q': search_query}
    form = SearchForm(initial=data)

    paginator = Paginator(search_results, settings.PHOTOS_PER_PAGE)
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
    try:
        response = HttpResponse(content_type="image/jpg")
        im.save(response, "JPEG")
    except OSError:
        response = HttpResponse(content_type="image/png")
        im.save(response, "PNG")
    return response


class PhotoViewAnnotated(TemplateView):

    def get(self, request, photo_id):
        photo = Photo.objects.get(pk=photo_id)
        image = settings.PHOTO_ROOT + photo.album.name + photo.file
        im = Image.open(image)
        draw = ImageDraw.Draw(im)
        boxes = json.loads(photo.get_prop('face_annotate'))
        for box in boxes:
            draw.rectangle(box, width=5)
        response = HttpResponse(content_type="image/jpg")
        im.save(response, "JPEG")
        return response


def photo_favourites_view(request):
    photos = Photo.objects.filter(photoprops__name='favourite', photoprops__value='true').order_by('-date')
    paginator = Paginator(photos, settings.PHOTOS_PER_PAGE)
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
            default_tags = form.cleaned_data.get("default_tags")
            default_date = form.cleaned_data.get("default_date")
            directory = form.cleaned_data.get("directory")
            if not directory.endswith('/'):
                directory = directory + '/'
            out = StringIO()
            management.call_command('upload_album',
                                    directory=directory,
                                    defaulttags=default_tags,
                                    defaultdate=default_date,
                                    stdout=out)
            album_id = int(out.getvalue())
            #management.call_command('face_detection',
            #                       album=album_id)
            return HttpResponseRedirect(reverse('photo:album', kwargs={'album_id': album_id}))
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
        return HttpResponseRedirect(reverse('photo:album',
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

    return redirect('photo:album', album_id=photo.album.id)


def photo_star_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    photo.set_prop('favourite', 'true')
    return redirect('photo:album', album_id=photo.album.id)


def photo_unstar_view(request, photo_id):
    photo = Photo.objects.get(pk=photo_id)
    photo.set_prop('favourite', 'false')
    return redirect('photo:album', album_id=photo.album.id)


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



def album_exif(request, album_id):
    album = Album.objects.get(id=album_id)
    photos = Photo.objects.filter(album=album)
    for photo in photos:
        rewrite_exif(photo)
    return redirect('photo:album', album_id=album_id)



def scan_folder_async(request):
    if request.method == 'POST':
        form = ScanFolderForm(request.POST)
        if form.is_valid():
            default_tags = form.cleaned_data.get("default_tags")
            default_date = form.cleaned_data.get("default_date")
            directory = form.cleaned_data.get("directory")
            if not directory.endswith('/'):
                directory = directory + '/'
            # Create Task
            upload_task = UploadAlbum.delay(directory, default_tags, default_date)
            # Get ID
            task_id = upload_task.task_id
            return render(request, 'photo/async_upload.html',
                          {'task_id': task_id, 'form': form, 'title': _(u'Scan Folder - Async')})
    else:
        data = {}
        data['default_date'] = timezone.now()
        data['directory'] = '/' + str(timezone.now().year) + '/'
        data['default_tags'] = ''
        form = ScanFolderForm(initial=data)

    return render(request, 'photo/async_upload.html',
                  {'form': form, 'title': _(u'Scan Folder - Async')})
