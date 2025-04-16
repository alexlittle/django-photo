
import os
import json

from io import StringIO

from PIL import Image, ImageDraw



from django.conf import settings
from django.core import management
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Max, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, ListView, View,FormView


from photo.asynctasks.face_detection import FaceDetection
from photo.forms import ScanFolderForm, EditPhotoForm, SearchForm, UpdateTagsForm
from photo.lib import add_tags, add_or_update_xmp_metadata
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


class AlbumView(ListView):
    template_name = 'photo/album.html'
    context_object_name = 'photos'
    paginate_by = settings.PHOTOS_PER_PAGE

    def dispatch(self, request, *args, **kwargs):
        self.album = get_object_or_404(Album, pk=kwargs['album_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        photos = Photo.objects.filter(album=self.album).order_by('date', 'file')

        if self.request.GET.get('view', '') == 'print':
            photos = photos.exclude(photoprops__name='exclude.album.export', photoprops__value='true')

        return photos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = self.album
        context['photo_count'] = self.get_queryset().count()
        context['photos_checked'] = self.request.GET.getlist('photo_id', [])

        if self.request.GET.get('detect', None) is not None:
            upload_task = FaceDetection.delay(self.album.id)
            context['task_id'] = upload_task.task_id

        return context


class TagSlugView(ListView):
    template_name = 'photo/tag.html'
    context_object_name = 'photos'
    paginate_by = settings.PHOTOS_PER_PAGE  # Enables built-in pagination

    def get_queryset(self):
        slug_list = self.kwargs['slug'].split('+')
        return (
            Photo.objects.filter(phototag__tag__slug__in=slug_list)
            .annotate(count=Count('id'))
            .filter(count=len(slug_list))
            .order_by('date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug_list = self.kwargs['slug'].split('+')
        context['tags'] = Tag.objects.filter(slug__in=slug_list)
        context['photos_checked'] = self.request.GET.getlist('photo_id', [])
        return context


class CloudView(TemplateView):
    template_name = 'photo/cloud.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Cloud'),
            'tags': Tag.objects.all().order_by('name'),
            'categories': TagCategory.objects.all().order_by('name'),
        })
        return context


class MapView(TemplateView):
    template_name = 'photo/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.filter(tagcategory__name='Location', tagprops__name='source', tagprops__value='me') \
            .exclude(tagprops__name='lat', tagprops__value='0') \
            .exclude(tagprops__name='map.display', tagprops__value='false') \
            .distinct()

        context.update({
            'title': _('Map'),
            'tags': tags
        })
        return context


class CloudCategoryView(TemplateView):
    template_name = 'photo/cloud_category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = kwargs['category']
        tags = Tag.objects.filter(tagcategory__name=category) \
            .values('id', 'name', 'slug') \
            .annotate(count=Count('phototag')).order_by('name')

        context.update({
            'title': _('Cloud'),
            'tags': tags
        })
        return context


class SearchView(ListView):
    template_name = 'photo/search.html'
    context_object_name = 'results'
    paginate_by = settings.PHOTOS_PER_PAGE  # Enables automatic pagination

    def get_queryset(self):
        search_query = self.request.GET.get('q', '').strip()

        if search_query:
            search_id_results = CombinedSearch.objects.combined_search(search_query)
            search_ids = [result['id'] for result in search_id_results]
        else:
            search_ids = []

        return Photo.objects.filter(pk__in=search_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '').strip()
        form = SearchForm(initial={'q': search_query})
        context['photos_checked'] = self.request.GET.getlist('photo_id', [])
        context.update({
            'form': form,
            'query': search_query,
            'total_results': self.get_queryset().count(),
        })
        return context


class PhotoView(View):
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        image_path = os.path.join(settings.PHOTO_ROOT, photo.album.name.lstrip("/"), photo.file)

        if not os.path.exists(image_path):
            raise Http404("Image not found")

        im = Image.open(image_path)
        response = HttpResponse(content_type="image/jpeg")

        try:
            im.save(response, "JPEG")
        except OSError:
            response = HttpResponse(content_type="image/png")
            im.save(response, "PNG")

        return response

class PhotoViewAnnotated(View):
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        image_path = os.path.join(settings.PHOTO_ROOT, photo.album.name.lstrip("/"), photo.file)

        with Image.open(image_path) as im:
            draw = ImageDraw.Draw(im)
            boxes = json.loads(photo.get_prop('face_annotate'))
            for box in boxes:
                draw.rectangle(box, width=5)

            response = HttpResponse(content_type="image/jpeg")
            im.save(response, "JPEG")

        return response


class PhotoFavouritesView(ListView):
    model = Photo
    template_name = 'photo/favourites.html'
    context_object_name = 'photos'
    paginate_by = settings.PHOTOS_PER_PAGE

    def get_queryset(self):
        return Photo.objects.filter(photoprops__name='favourite', photoprops__value='true').order_by('-date')


class ScanFolderView(FormView):
    template_name = 'photo/scan.html'
    form_class = ScanFolderForm
    success_url = '/'  # Placeholder, to be updated dynamically

    def get_initial(self):
        initial = super().get_initial()
        initial['default_date'] = timezone.now()
        initial['directory'] = '/' + str(timezone.now().year) + '/'
        initial['default_tags'] = ''
        return initial

    def form_valid(self, form):
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

        self.success_url = reverse('photo:album', kwargs={'album_id': album_id})
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, title=_('Scan Folder')))


class PhotoEditView(View):
    template_name = 'photo/edit.html'
    form_class = EditPhotoForm

    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        tags = Tag.objects.filter(phototag__photo=photo).values_list('name', flat=True)
        data = {
            'tags': ", ".join(tags),
            'title': photo.title,
            'date': photo.date,
        }
        form = self.form_class(initial=data)
        context = {
            'form': form,
            'title': _(u'Edit Photo'),
            'photo': photo,
        }
        return render(request, self.template_name, context)

    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        form = self.form_class(request.POST)

        if form.is_valid():
            PhotoTag.objects.filter(photo=photo).delete()
            new_tags = form.cleaned_data.get("tags")
            add_tags(photo, new_tags)
            photo.title = form.cleaned_data.get("title")
            photo.date = form.cleaned_data.get("date").replace(hour=photo.date.hour, minute=photo.date.minute)
            photo.save()
            add_or_update_xmp_metadata(photo)
            return redirect('photo:album', album_id=photo.album.id)

        context = {
            'form': form,
            'title': _(u'Edit Photo'),
            'photo': photo,
        }
        return render(request, self.template_name, context)


class PhotoSetCoverView(View):
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        photos = Photo.objects.filter(album=photo.album, album_cover=True)

        for p in photos:
            p.album_cover = False
            p.save()

        photo.album_cover = True
        photo.save()

        return redirect('photo:album', album_id=photo.album.id)


class PhotoStarView(View):
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        photo.set_prop('favourite', 'true')
        return redirect('photo:album', album_id=photo.album.id)


class PhotoUnstarView(View):
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        photo.set_prop('favourite', 'false')
        return redirect('photo:album', album_id=photo.album.id)


class PhotoUpdateTagsView(FormView):
    template_name = 'photo/update_tags.html'
    form_class = UpdateTagsForm

    def get_initial(self):
        """Pre-fill the form with query parameters."""
        initial = super().get_initial()
        initial['next'] = self.request.GET.get("next", "/")
        return initial

    def get_photo_ids(self):
        """Retrieve photo IDs from request."""
        return self.request.GET.getlist('photo_id', [])

    def form_valid(self, form):
        """Process the form when submitted."""
        photo_ids = self.get_photo_ids()
        action = form.cleaned_data.get("action")
        update_tags = form.cleaned_data.get("tags", "")
        date = form.cleaned_data.get("date")
        next_url = form.cleaned_data.get("next")
        tags = [x.strip() for x in update_tags.split(',') if x.strip()]

        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            for photo_id in photo_ids:
                try:
                    photo = Photo.objects.get(id=photo_id)
                    if action == "delete":
                        PhotoTag.objects.filter(photo=photo, tag=tag).delete()
                    elif action == "add":
                        PhotoTag.objects.get_or_create(photo=photo, tag=tag)
                        add_or_update_xmp_metadata(photo)
                except Photo.DoesNotExist:
                    continue

        if action == "change_date":
            for photo_id in photo_ids:
                try:
                    photo = Photo.objects.get(id=photo_id)
                    photo.date = date
                    photo.save()
                    add_or_update_xmp_metadata(photo)
                except Photo.DoesNotExist:
                    continue

        if action == "change_album":
            new_album = get_object_or_404(Album, pk=form.cleaned_data.get("album"))
            for photo_id in photo_ids:
                try:
                    photo = Photo.objects.get(id=photo_id)
                    old_path = os.path.join(settings.PHOTO_ROOT, photo.album.name, photo.file)
                    new_path = os.path.join(settings.PHOTO_ROOT, new_album.name, photo.file)
                    os.rename(old_path, new_path)
                    photo.album = new_album
                    photo.save()
                except (Photo.DoesNotExist, FileNotFoundError):
                    continue

        # Redirect to the next page with updated photo IDs
        url_params = '&'.join([f'photo_id={x}' for x in photo_ids])
        return HttpResponseRedirect(f"{next_url}&{url_params}")

    def form_invalid(self, form):
        """Handle form errors."""
        return self.render_to_response(self.get_context_data(form=form, title=_('Update Tags')))



class AlbumExifUpdateView(View):
    def get(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        photos = Photo.objects.filter(album=album)

        for photo in photos:
            add_or_update_xmp_metadata(photo)

        return redirect('photo:album', album_id=album_id)



class ScanFolderAsyncView(FormView):
    template_name = 'photo/async_upload.html'
    form_class = ScanFolderForm

    def get_initial(self):
        """Pre-fill the form with default values."""
        initial = super().get_initial()
        initial['default_date'] = timezone.now()
        initial['directory'] = '/' + str(timezone.now().year) + '/'
        initial['default_tags'] = ''
        return initial

    def form_valid(self, form):
        """Handle form submission and start the async task."""
        default_tags = form.cleaned_data.get("default_tags")
        default_date = form.cleaned_data.get("default_date")
        directory = form.cleaned_data.get("directory")

        if not directory.endswith('/'):
            directory += '/'

        # Start Celery async task
        upload_task = UploadAlbum.delay(directory, default_tags, default_date)

        # Get task ID for tracking
        task_id = upload_task.task_id

        return self.render_to_response(self.get_context_data(form=form, task_id=task_id, title=_('Scan Folder - Async')))

    def form_invalid(self, form):
        """Render form again with errors."""
        return self.render_to_response(self.get_context_data(form=form, title=_('Scan Folder - Async')))
