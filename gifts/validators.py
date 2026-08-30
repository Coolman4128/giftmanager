import math

from django import forms
from django.core.validators import URLValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class UnlimitedURLValidator(URLValidator):
    """A URL validator without Django's 2048 character cap.

    Gift links are often long affiliate or tracking URLs, so we check the shape
    of the URL but never its length.
    """

    max_length = math.inf


class UnlimitedURLFormField(forms.URLField):
    """Form counterpart to :class:`UnlimitedURLValidator`."""

    default_validators = [UnlimitedURLValidator()]
