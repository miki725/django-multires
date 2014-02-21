from __future__ import unicode_literals, print_function
import os
import six
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.db import models
from uuid import uuid4
from .signals import multires_source_created

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    add_introspection_rules = None


def MultiresRecipe():
    from .models import MultiresRecipe

    return MultiresRecipe


def MultiresImage():
    from .models import MultiresImage

    return MultiresImage


class SourceImageField(ImageField):
    """
    Same as Django's ImageField except this makes sure
    to never save the file.
    """

    def pre_save(self, model_instance, add):
        """
        Avoids saving the file in storage since source images
        will be saved by source model instances.
        """
        return models.Field.pre_save(self, model_instance, add)


class LazyMultiresImageFieldFile(ImageFieldFile):
    """
    Similar to Django's default ``ImageFieldFile`` except
    how this class calculates the url.
    If image file is not created image yet, a lazy
    url for processing image when accessed is returned.
    This allows to get the URL immediately without any
    computational overhead.

    .. warning::
        If the url ``multires:lazy_multires`` is not mapped,
        and the image is not processed yet, the source image
        URL will be returned.
    """

    @property
    def url(self):
        try:
            return self._get_url()
        except ValueError:
            uuid = getattr(self.instance, self.field.uuid_field, None)
            if not uuid:
                raise ValueError('Model.{0} does not have uuid value '
                                 'which is required to generate lazy url.'
                                 ''.format(self.field.uuid_field))
            try:
                return reverse('multires:lazy_multires', kwargs={'uuid': uuid})
            except NoReverseMatch:
                return getattr(self.instance, self.field.source_field).url


class LazyMultiresImageField(ImageField):
    """
    Lazy image field in a sense that if there is no file processed yet,
    and when its url is requested, it returns a generator url which
    when accessed will process the image. This allows to lazily
    process images as they are accessed.

    Parameters
    ----------
    uuid_field : str
        Name of field from which the uuid will  be retrieved to
        generate the lazy image url.
    size_field : str
        Name of field where size should be stored in bytes
    """
    attr_class = LazyMultiresImageFieldFile

    def __init__(self, uuid_field=None, source_field=None, size_field=None,
                 *args, **kwargs):
        self.uuid_field = uuid_field
        self.source_field = source_field
        self.size_field = size_field
        self.upload_to_path = kwargs['upload_to']
        kwargs['upload_to'] = self.random_upload_to(kwargs['upload_to'])

        super(LazyMultiresImageField, self).__init__(*args, **kwargs)

    def random_upload_to(self, path):
        """
        Get the upload_to handler which will generate unique
        filename for each image. If model instance already has
        uuid value, it will use that for filename.
        """

        def f(instance, filename):
            ext = filename.split('.')[-1]
            if getattr(settings, 'MULTIRES_LAZY_ENTROPY', True):
                uuid = getattr(instance, self.uuid_field, uuid4().hex)
            else:
                uuid = uuid4().hex
            filename = '{0}.{1}'.format(uuid, ext)
            return os.path.join(path, filename)

        return f

    def update_dimension_fields(self, instance, force=False, *args, **kwargs):
        """
        In addition to updating image dimensions, this method also
        updates the image size in bytes.
        The code logic is copied from how Django handles updating
        width and height attributes.
        """
        super(LazyMultiresImageField, self) \
            .update_dimension_fields(instance, force, *args, **kwargs)

        if not self.size_field:
            return

        file = getattr(instance, self.attname)
        if not file and not force:
            return

        size_field_filled = self.size_field and getattr(instance, self.size_field)
        if size_field_filled and not force:
            return

        if file:
            size = file.size
        else:
            size = None

        if self.size_field:
            setattr(instance, self.size_field, size)


class MultiresImageFieldFile(ImageFieldFile):
    """
    ImageFieldFile subclass (what is returned for ``models.ImageField``)
    which enables interaction with Multires images.
    """

    def _normalize_recipe(self, recipe):
        """
        Helper method for normalizing recipe depending on its
        data-type.

        Parameters
        ----------
        recipe : str, int, MultiresRecipe

        Returns
        -------
        recipe : int, MultiresRecipe
            Normalized recipe value to either an ``int`` for
            primary key of the recipe or ``MultiresRecipe`` instance.
        """
        if isinstance(recipe, six.string_types):
            recipe = MultiresRecipe().objects.get(namespace=self.field.namespace,
                                                  title=recipe)
        assert isinstance(recipe, (MultiresRecipe(), int))
        return recipe

    def _get_recipe_filter_kwarg(self, recipe):
        """
        Get filter kwargs for django queryset filters to filter
        by the recipe. This is useful because if the recipe is
        an integer, then the filter key is ``recipe_id`` whereas
        it should be ``recipe`` for everything else.
        """
        return {
            '{0}'.format('recipe_id'
                         if isinstance(recipe, int)
                         else 'recipe'): recipe
        }

    def _init_multires_image(self, recipe):
        """
        Initialize an multires image model instance with
        all required parameters.
        """
        kwargs = {
            'source': self.name,
            'processed': False,
        }
        kwargs.update(self._get_recipe_filter_kwarg(recipe))
        return MultiresImage()(**kwargs)

    def get_all_multires_recipes(self, automatic_only=False):
        """
        Get all recipes for the namespace as this image
        is defined for.

        Parameters
        ----------
        automatic_only : bool, optional
            Whether to only the automatic recipes.
        """
        filter_kwargs = {
            'namespace': self.field.namespace,
        }
        if automatic_only:
            filter_kwargs.update({
                'automatic': True
            })
        return MultiresRecipe().objects.filter(**filter_kwargs)

    def get_all_multires_images(self,
                                existing_only=False,
                                processed_only=False,
                                automatic_only=False,
                                async=True, save=True):
        """
        Get all multires images for this source image.

        Parameters
        ----------
        existing_only : bool, optional
            Whether to get only already saved multires images.
            Default is ``False``.
        processed_only : bool, optional
            Whether to get only already processed multires images.
            Default is ``False``.
        automatic_only : bool, optional
            When making temporary images for all recipes, conditional
            whether to only generate them for automatic recipes.
        async : bool, optional
            Refer to ``get_multires_image`` docs as
            Default is ``True``.
        save : bool, optional
            Refer to ``get_multires_image`` docs.
            Default is ``True``.
        """
        if existing_only:
            filter_kwargs = {
                'recipe__namespace': self.field.namespace,
                'source': self.name,
            }
            if processed_only:
                filter_kwargs.update({
                    'processed': True,
                })
            return MultiresImage().objects.filter(**filter_kwargs)

        multires_images = list(
            MultiresImage().objects
            .filter(recipe__namespace=self.field.namespace,
                    source=self.name)
            .select_related('recipe')
        )

        # find any missing multires images and add them if any
        missing_recipes = self.get_all_multires_recipes(automatic_only) \
            .exclude(id__in=map(lambda i: i.recipe_id, multires_images))

        if len(missing_recipes) > 0:
            for recipe in missing_recipes:
                multires_images.append(self.get_multires_image(
                    recipe=recipe, async=async, save=save, try_lookup=False
                ))

        return multires_images

    def get_multires_image(self, recipe, async=True, save=True, try_lookup=True):
        """
        Get multires image for specified recipe.

        Parameters
        ----------
        recipe : int, str, MultiresRecipe
            Recipe to lookup. This value is normalized by ``_normalize_recipe``.
        async : bool, optional
            When ``False`` this becomes blocking operation while image
            will be processed and saved.
            When ``True``, temporarily multires image is constructed
            without processing it. However the url for image can still
            be retrieved as long as save parameter is ``True`` since
            the returned url will be lazy (when accessed it will
            process the image).
            Default is ``True``.
        save : bool, optional
            If multires image is already not in the db, whether save
            the not processed temporary multires image into db.
            Please note that this is necessary in order to be able
            to get the lazy url since uuid is generated while saving.
        try_lookup : bool, optional
            If ``True``, try to lookup the multires image in the db.
            Useful to set to ``False``, when there is a guarantee
            that multires image will not be found hence allows
            to save a db query.
            Default is ``True``.
        """
        recipe = self._normalize_recipe(recipe)

        if try_lookup:
            try:
                kwargs = self._get_recipe_filter_kwarg(recipe)
                return self.get_all_multires_images().get(**kwargs)
            except MultiresImage().DoesNotExist:
                pass

        image = self._init_multires_image(recipe)
        if not async:
            image.process()
        if save or not async:
            image.save()

        return image


class MultiresImageField(ImageField):
    """
    Multires interface field. In another words, this field should
    be used to enable multires functionality on regular image fields.

    Parameters
    ----------
    namespace : str
        Namespace to use for recipes
    """
    attr_class = MultiresImageFieldFile
    description = 'Multi-resolution Image'

    def __init__(self, *args, **kwargs):
        self.namespace = kwargs.pop('namespace', '')
        super(MultiresImageField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        """
        Attached necessary garbage collection signals.
        """
        super(MultiresImageField, self).contribute_to_class(cls, name)

        models.signals.post_save.connect(self.handle_source_created, sender=cls)
        models.signals.post_delete.connect(self.handle_source_delete, sender=cls)
        if all([callable(getattr(cls, 'is_dirty', None)),
                callable(getattr(cls, 'get_dirty_fields', None))]):
            models.signals.post_save.connect(self.handle_source_change, sender=cls)

    def handle_source_created(self, instance, *args, **kwargs):
        """
        Trigger ``multires_source_created`` signal.
        """
        multires_source_created.send_robust(sender=instance, field_name=self.attname)

    def handle_source_change(self, instance, *args, **kwargs):
        """
        Delete all multires images when source image is replaced.
        """
        if instance.is_dirty():
            name = self.attname
            old_value = instance.get_dirty_fields().get(name, None)
            if old_value:
                method = getattr(old_value, 'get_all_multires_images', None)
                if method and callable(method):
                    method(existing_only=True).delete()

    def handle_source_delete(self, instance, *args, **kwargs):
        """
        Delete all multires images when source image is deleted.
        """
        field = getattr(instance, self.attname, None)
        if field:
            method = getattr(field, 'get_all_multires_images', None)
            if method and callable(method):
                method(existing_only=True).delete()


if add_introspection_rules:
    add_introspection_rules(
        [
            [
                (LazyMultiresImageField,),
                (),
                {'upload_to': ('upload_to_path', {})}
            ],
        ],
        [
            '^multires\.fields',
        ]
    )
