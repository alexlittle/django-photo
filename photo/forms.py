import os

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FieldWithButtons
from crispy_forms.layout import Button, Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Row


class ScanFolderForm(forms.Form):
    directory = forms.CharField(
                required=True,
                error_messages={'required': _('Please enter a directory')},)
    default_date = forms.DateField(
                required=True,
                error_messages={'required': _('Please enter a default date')},)
    default_tags = forms.CharField(
                required=True,
                error_messages={'required': _('Please enter at least one tag')},)
    
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

    tags = forms.CharField(
                required=True,
                error_messages={'required': _('Please enter at least one tag')},)
    
    def __init__(self, *args, **kwargs):
        super(EditPhotoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
                'tags',
                Div(
                   Submit('submit', _(u'Update'), css_class='btn btn-default'),
                   css_class='col-lg-offset-2 col-lg-4',
                ),
            )
    def clean(self):
        cleaned_data = super(EditPhotoForm, self).clean()
        return cleaned_data