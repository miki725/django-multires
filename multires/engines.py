from __future__ import unicode_literals, print_function
from django.core.files.base import ContentFile
from functools import wraps
from . import processors


class BaseEngine(object):
    def __init__(self, recipe=None):
        self.recipe = recipe

    def pre(self, image):
        """
        Hook for pre-processing of image.
        """
        return image

    def post(self, image):
        """
        Hook for post-processing of image.
        """
        return image

    def process(self, image):
        raise NotImplementedError

    def full_process(self, image):
        image = self.pre(image)
        image = self.process(image)
        image = self.post(image)
        return image

    def save(self, image):
        raise NotImplementedError

    def __call__(self, image, recipe):
        self.recipe = recipe
        image = self.full_process(image)
        file = self.save(image)
        return file

    @classmethod
    def as_callable(cls):
        @wraps(cls)
        def wrapper(*args, **kwargs):
            return cls()(*args, **kwargs)

        return wrapper


class DefaultEngine(BaseEngine):
    FILE_TYPE_EXT_MAPPING = {
        'jpeg': 'jpg',
        'png': 'png',
    }

    def process(self, image):
        if self.recipe.flip:
            image = processors.flip_processor(
                image,
                flip=self.recipe.flip,
            )

        if self.recipe.rotate:
            rotate_kwargs = {
                'degrees': self.recipe.rotate,
                'color': self.recipe.rotate_color or None,
                'preserve_transparency': False,
            }
            if not self.recipe.rotate_crop:
                rotate = processors.rotate_processor
                if self.recipe.file_type == 'png':
                    rotate_kwargs.update({
                        'preserve_transparency': False,
                    })
            else:
                rotate = processors.rotate_crop_processor
                rotate_kwargs.update({
                    'crop_mode': self.recipe.rotate_crop
                })
            image = rotate(image, **rotate_kwargs)

        if self.recipe.crop:
            image = processors.crop_processor(
                image,
                crop_box=self.recipe.crop,
            )

        if self.recipe.width or self.recipe.height:
            image = processors.resize_processor(
                image,
                width=self.recipe.width or image.size[0],
                height=self.recipe.height or image.size[1],
                fit=self.recipe.fit,
                upscale=self.recipe.upscale
            )

        return image

    def save(self, image):
        file_type = self.recipe.file_type
        name = '.{0}'.format(self.FILE_TYPE_EXT_MAPPING.get(file_type, file_type))
        fid = ContentFile(b'', name=name)

        save_kwargs = {}
        if file_type in ['jpeg'] and self.recipe.quality:
            save_kwargs.update({
                'quality': self.recipe.quality,
            })

        # normalize mode
        if self.recipe.file_type == 'jpeg':
            if image.mode not in ['RGB', 'RGBA']:
                image = image.convert('RGB')

        image.save(fid, format=file_type, **save_kwargs)

        return fid
