from __future__ import unicode_literals, print_function
import six
from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django_auxilium.models import (BaseModel,
                                    MultipleValuesField,
                                    UUIDModel,
                                    file_field_auto_delete,
                                    file_field_auto_change_delete)
from .fields import SourceImageField, LazyMultiresImageField
from .files import generate_multires_image_file


@python_2_unicode_compatible
class MultiresRecipe(BaseModel):
    """
    Attributes
    ----------
    title : str
        Title of the recipe
    description : str
        Description of the recipe
    namespace : str
        Namespace allows to classify recipes into groups so that
        different source models can use a different set of recipes.
    automatic : bool
        If ``True``, all new images for the namespace will automatically
        resize with this recipe. Default is True.
    ad_hoc : bool
        If ``True``, this recipe is meant to be used only once as
        an ad-hoc recipe to process a specific image.
    flip : str
        How and if the image should be flipped. Allowed options are:

        :``''``: not flipped
        :``x``: flipped around horizontal axis - upside-down
        :``y``: flipped around vertical axis - left-right

        By default image is not flipped.
    rotate : int
        Degrees by how much the image should be rotated. Please note
        that this is in degrees, not radians.
    rotate_crop : str
        If rotated image should be cropped to avoid any non-image areas.
        Default is ``''``.

        :``''``: Do not crop.
        :``aspect_ratio``: Crop while preserving aspect ratio
        :``max_area``: Crop while ensuring maximum area of cropped result
    rotate_color : list
        If the image is not cropped after rotating, RGBA color to use
        to fill in the background. If no color is provided, default PIL
        color will be used. Please note that even if image is not
        cropped after rotation, there is still a possibility that
        final image will not include any non-image regions due to
        regular crop parameters.
    crop : list
        Crop bounding box relative to the edges of how much the image
        should be cropped. The order of parameters is ``(x1, y1, x2, y2)``.
    width : int
        Maximum width of the resized image bounding box
    height : int
        Maximum height of the resized image bounding box
    upscale : bool
        If ``True``, if the original image is smaller than the resize
        dimension, it will be up-scaled to the required resolution.
        Default is ``False``.
    fit : str
        If the aspect ratio of the input image and bounding box are
        not the same aspect ratio, how to fit it into the bounding box.
        Allowed are ``fit``, (``crop``, ``center``, ``fill``), ``top``,
        ``left``, ``right``, ``bottom``. Default is ``fit``.
    file_type : str
        The filetype of under which processed image should be saved.
        Supported filetypes are ``jpeg`` and ``png``.
        Default is ``jpeg``.
    quality : int
        If the filetype is a lossy fileformat, the quality under which
        to save the file.
    """
    FLIP_CHOICES = (
        ('', 'none'),
        ('x', 'upside-down'),
        ('y', 'left-right'),
    )
    ROTATE_CROP_CHOICES = (
        ('', 'none'),
        ('aspect_ratio', 'aspect ratio'),
        ('max_area', 'maximum area'),
    )
    FIT_CHOICES = (
        ('fit', 'fit'),
        ('center', 'center'),
        ('top', 'top'),
        ('left', 'left'),
        ('right', 'right'),
        ('bottom', 'bottom'),
    )
    FILE_TYPES = (
        ('jpeg', 'JPG'),
        ('png', 'PNG'),
    )

    title = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    namespace = models.CharField(max_length=128, blank=True)

    # automation
    automatic = models.BooleanField(default=True)
    ad_hoc = models.BooleanField(default=False)

    # image processing
    flip = models.CharField(max_length=4, choices=FLIP_CHOICES,
                            blank=True, default='')
    rotate = models.SmallIntegerField(blank=True, null=True)
    rotate_crop = models.CharField(max_length=16, choices=ROTATE_CROP_CHOICES,
                                   blank=True, default='')
    rotate_color = MultipleValuesField(max_length=16, blank=True,
                                       min_values=4, max_values=4,
                                       mapping=lambda v: min(255, max(0, int(v))),
                                       help_text='R,G,B,A')
    crop = MultipleValuesField(max_length=32, blank=True,
                               min_values=4, max_values=4, mapping=int,
                               help_text='x1,y1,x2,y2')
    width = models.PositiveSmallIntegerField(null=True)
    height = models.PositiveSmallIntegerField(null=True)
    upscale = models.BooleanField(default=False)
    fit = models.CharField(max_length=8, choices=FIT_CHOICES, default='fit')

    # saving
    file_type = models.CharField(max_length=4, choices=FILE_TYPES, default='jpeg')
    quality = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta(object):
        unique_together = (
            ('namespace', 'title'),
        )

    def __str__(self):
        suffix = '{0} @ {1}'.format(self.title or 'None',
                                    self.namespace or 'None')
        if not self.ad_hoc:
            return suffix
        else:
            return '_{0}'.format(suffix)


@python_2_unicode_compatible
@file_field_auto_delete('image')
@file_field_auto_change_delete('image')
class MultiresImage(DirtyFieldsMixin, UUIDModel, BaseModel):
    """
    Attributes
    ----------
    source : Image
        The source image for which multires is created.
    recipe : MultiresRecipe
        The recipe for which the image is created.
    image : Image
        Processed image as per the recipe
    width : int
        Final width of the processed image
    height : int
        Final height of the processed image
    size : int
        Final size in bytes of the processed image
    """
    source = SourceImageField(upload_to='multires/sources', db_index=True)
    recipe = models.ForeignKey(MultiresRecipe, related_name='images')
    processed = models.BooleanField(default=False)

    image = LazyMultiresImageField(upload_to='multires/images/',
                                   width_field='width',
                                   height_field='height',
                                   size_field='size',
                                   uuid_field='uuid',
                                   source_field='source',
                                   blank=True)
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    size = models.PositiveIntegerField(blank=True, null=True)

    class Meta(object):
        unique_together = (
            ('source', 'recipe'),
        )

    def process(self, save=True):
        if not self.recipe_id and not self.recipe or not self.source:
            raise ValueError('recipe and source are required to '
                             'process multires image')

        self.image = generate_multires_image_file(self.source, self.recipe)
        self.processed = True
        if save:
            self.save()

    def __str__(self):
        if self.recipe_id:
            result = '{0} for {1}'.format(six.text_type(self.recipe),
                                          six.text_type(self.source))
        else:
            result = six.text_type(self.source)
        return '{0}{1}'.format('+' if self.processed else '-', result)
