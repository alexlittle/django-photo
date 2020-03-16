import os

from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FieldWithButtons
from crispy_forms.layout import Layout, Submit, Div

from photo.models import Album

class ScanFolderForm(forms.Form):
    directory = forms.CharField(
                required=True,
                error_messages={'required': _('Please enter a directory')},)
    default_date = forms.DateField(
                required=True,
                error_messages={'required': _('Please enter a default date')},)
    default_tags = forms.CharField(
                required=True,
                error_messages={'required':
                                _('Please enter at least one tag')},)

    def __init__(self, *args, **kwargs):
        super(ScanFolderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('photo_scan')
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
                'directory',
                'default_date',
                'default_tags',
                Div(
                   Submit('submit', _(u'Upload'), css_class='btn btn-default'),
                   css_class='col-lg-offset-2 col-lg-4',
                ),
            )

    def clean(self):
        cleaned_data = super(ScanFolderForm, self).clean()
        directory = cleaned_data.get("directory")
        # Check directory exists
        if not os.path.isdir(settings.PHOTO_ROOT + directory):
            raise forms.ValidationError(_("Directory does not exist"))

        return cleaned_data


class EditPhotoForm(forms.Form):
    title = forms.CharField(
                required=False,)
    tags = forms.CharField(
                required=True,
                error_messages={'required':
                                _('Please enter at least one tag')},)
    date = forms.DateField(
                required=True,
                error_messages={'required': _('Please enter a valid date'),
                                'invalid': _('Please enter a valid date')},)

    def __init__(self, *args, **kwargs):
        super(EditPhotoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
                'title',
                'tags',
                Div('date', css_class='date-picker-row-fluid'),
                Div(
                   Submit('submit', _(u'Update'), css_class='btn btn-default'),
                   css_class='col-lg-offset-2 col-lg-4',
                ),
            )

    def clean(self):
        cleaned_data = super(EditPhotoForm, self).clean()
        return cleaned_data


class SearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        error_messages={'required':
                        _(u'Please enter something to search for')},)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = "GET"
        self.helper.form_class = 'form-horizontal'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            FieldWithButtons('q', Submit('submit', _(u'Go'),
                                         css_class='btn btn-default')),

        )


class UpdateTagsForm(forms.Form):
    UPDATE_ACTIONS = (('add', _(u'Add Tag/s')),
                      ('delete', _(u'Delete Tag/s')),
                      ('change_date', _(u'Change date')),
                      ('change_album', _(u'Move to album'))
                      )

    action = forms.ChoiceField(required=True,
                               choices=UPDATE_ACTIONS)
    tags = forms.CharField(required=False)
    date = forms.DateField(
                required=False,
                error_messages={'required': _('Please enter a valid date'),
                                'invalid': _('Please enter a valid date')},)
    album = forms.ChoiceField(choices=Album.objects
                              .all()
                              .order_by('name')
                              .values_list('id','name'))

    def __init__(self, *args, **kwargs):
        super(UpdateTagsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
                'action',
                'tags',
                Div('date', css_class='date-picker-row-fluid'),
                'album',
                Div(
                   Submit('submit', _(u'Update'), css_class='btn btn-default'),
                   css_class='col-lg-offset-2 col-lg-4',
                ),
            )

    def clean(self):
        cleaned_data = super(UpdateTagsForm, self).clean()
        return cleaned_data
