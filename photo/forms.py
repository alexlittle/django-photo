import os
from datetime import datetime

from crispy_forms.bootstrap import FieldWithButtons
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from photo.models import Album

VALID_DATE = "Please enter a valid date (YYYY-MM-DD) and optionally a time (HH:MM)."
DIV_SUBMIT_CLASS = "col-lg-offset-2 col-lg-4"
BTN_DEFAULT_CLASS = "btn btn-default"


def parse_date_and_time(value, form):
    """Parse 'YYYY-MM-DD[ HH:MM]'; sets form.time when a time was given and returns the date."""
    value = value.strip()
    if not value:
        return None
    for fmt, has_time in (("%Y-%m-%d %H:%M", True), ("%Y-%m-%d", False)):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if has_time:
            form.time = parsed.time()
        return parsed.date()
    raise forms.ValidationError(_(VALID_DATE))


class ScanFolderForm(forms.Form):
    directory = forms.CharField(
        required=True,
        error_messages={"required": _("Please enter a directory")},
    )
    default_date = forms.DateField(
        required=True,
        error_messages={"required": _("Please enter a default date")},
    )
    default_tags = forms.CharField(
        required=False,
        error_messages={"required": _("Please enter at least one tag")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-4"
        self.helper.layout = Layout(
            "directory",
            "default_date",
            "default_tags",
            Div(
                Submit("submit", _("Upload"), css_class=BTN_DEFAULT_CLASS),
                css_class=DIV_SUBMIT_CLASS,
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        directory = cleaned_data.get("directory")
        # Check directory exists
        if directory and not os.path.isdir(settings.PHOTO_ROOT + directory):
            raise forms.ValidationError(_("Directory does not exist"))

        return cleaned_data


class EditPhotoForm(forms.Form):
    title = forms.CharField(
        required=False,
    )
    tags = forms.CharField(
        required=True,
        error_messages={"required": _("Please enter at least one tag")},
    )
    date = forms.CharField(
        required=True,
        error_messages={"required": _(VALID_DATE)},
        help_text=_("YYYY-MM-DD, optionally followed by HH:MM (otherwise the time is kept)"),
    )

    def clean_date(self):
        """Parse the date; the time is returned in cleaned_data["time"] (None if not given)."""
        self.time = None
        return parse_date_and_time(self.cleaned_data.get("date", ""), self)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-4"
        self.helper.layout = Layout(
            "title",
            "tags",
            Div("date", css_class="date-picker-row-fluid"),
            Div(
                Submit("submit", _("Update"), css_class=BTN_DEFAULT_CLASS),
                css_class=DIV_SUBMIT_CLASS,
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["time"] = getattr(self, "time", None)
        return cleaned_data


class SearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        error_messages={"required": _("Please enter something to search for")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_method = "GET"
        self.helper.form_class = "form-horizontal"
        self.helper.field_class = "col-lg-8"
        self.helper.layout = Layout(
            FieldWithButtons("q", Submit("submit", _("Go"), css_class=BTN_DEFAULT_CLASS)),
        )


class UpdateTagsForm(forms.Form):
    UPDATE_ACTIONS = (
        ("add", _("Add Tag/s")),
        ("delete", _("Delete Tag/s")),
        ("change_date", _("Change date")),
        ("change_album", _("Move to album")),
        ("delete_photo", _("Delete Photo/s")),
    )

    action = forms.ChoiceField(required=True, choices=UPDATE_ACTIONS)
    tags = forms.CharField(required=False)
    date = forms.CharField(
        required=False,
        help_text=_("YYYY-MM-DD, optionally followed by HH:MM (otherwise the time is kept)"),
    )
    album = forms.ChoiceField(
        choices=Album.objects.all().order_by("name").values_list("id", "name")
    )
    next = forms.CharField(required=True)

    def clean_date(self):
        """Parse the date; the time is returned in cleaned_data["time"] (None if not given)."""
        value = self.cleaned_data.get("date", "").strip()
        self.time = None
        if not value:
            return None
        for fmt, has_time in (("%Y-%m-%d %H:%M", True), ("%Y-%m-%d", False)):
            try:
                parsed = datetime.strptime(value, fmt)
            except ValueError:
                continue
            if has_time:
                self.time = parsed.time()
            return parsed.date()
        raise forms.ValidationError(_(VALID_DATE))

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["time"] = getattr(self, "time", None)
        if cleaned_data.get("action") == "change_date" and not cleaned_data.get("date"):
            self.add_error("date", _(VALID_DATE))
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["album"].choices = (
            Album.objects.all().order_by("name").values_list("id", "name")
        )
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-4"
        self.helper.layout = Layout(
            "action",
            "tags",
            Div("date", css_class="date-picker-row-fluid"),
            "album",
            Field("next", type="hidden"),
            Div(
                Submit("submit", _("Update"), css_class=BTN_DEFAULT_CLASS),
                css_class=DIV_SUBMIT_CLASS,
            ),
        )
