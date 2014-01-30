from __future__ import unicode_literals, print_function
import six
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django_auxilium.utils.importlib import dynamic_import
from django_auxilium.utils.functools import cache
from PIL import Image


@cache
def get_engine():
    return dynamic_import(
        getattr(settings, 'MULTIRES_ENGINE', 'multires.engines.DefaultEngine')
    ).as_callable()


def generate_multires_image_file(image, recipe, engine=None):
    engine = engine or get_engine()

    if isinstance(image, six.string_types):
        image = Image.open(image)

    elif isinstance(image, ImageFieldFile):
        if image.closed:
            image.open()
        image.seek(0)
        image = Image.open(image)
        image.seek(0)

    return engine(image, recipe)
