"""
Collection of image processing algorithms/processors
"""
from __future__ import unicode_literals, print_function
import math
from functools import wraps
from PIL import Image
from .utils import AttrDict


class BaseProcessor(object):
    """
    Base class for image processors.
    Must implement ``process`` method.

    Also ``prep``, ``pre`` and ``post`` hook methods
    can be customized.

    Do not use a processor class directly but use the
    process callable. For example::

        # don't do this
        BaseProcessor()(image, ...)
        # but do this instead
        processor = BaseProcessor.as_callable()
        processor(image, ...)
    """
    DEFAULTS = {}

    def prep(self, image, options):
        """
        Prepares the class for processing.
        By default sets the options and sets the input image size
        for easy access.
        """
        self.options = AttrDict(self.DEFAULTS)
        self.options.update(options)

        self.input_size = image.size
        self.input_width, self.input_height = self.input_size

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

    def __call__(self, image, **options):
        self.prep(image, options)
        image = self.pre(image)
        image = self.process(image)
        image = self.post(image)
        return image

    @classmethod
    def as_callable(cls):
        """
        Get the process callable which each time creates an
        instance of a processor class.

        This is useful because each processor can implement custom
        helper methods which for ease of use can store various states
        as class attributes therefore each time a processor needs
        to be used, a new processor class instance must be created.
        This is the function of this method.
        """

        @wraps(cls)
        def wrapper(*args, **kwargs):
            return cls()(*args, **kwargs)

        return wrapper


class AnchorCropProcessorMixin(object):
    """
    Mixin with a helper method to get crop box around an anchor point.
    """

    def get_crop_box(self, image, width, height, anchor='center'):
        """
        Get crop box coordinates for the image to be cropped around
        the anchor point with the cropped image being given width and height.

        Parameters
        ----------
        image : Image
            PIL Image
        width : int
            Width of cropped image
        height : int
            Height of cropped image
        anchor : str
            The anchor point around which input image will be cropped.

            Allowed values are:

            :``center``, ``crop``, ``fill``: Crop around center
            :``top``: Crop from top
            :``left``: Crop from left
            :``right``: Crop from right
            :``bottom``: Crop from bottom

        Returns
        -------
        crop_box : tuple
            PIL compatible crop box - ``(x1, y1, x2, y2)``
        """
        image_size = image.size
        w, h = image_size

        if width > w:
            width = w
        if height > h:
            height = h

        center = int(w * 0.5), int(h * 0.5)

        if anchor in ['center', 'crop', 'fill']:
            x1 = int(center[0] - width * 0.5)
            y1 = int(center[1] - height * 0.5)
        elif anchor == 'top':
            x1 = int(center[0] - width * 0.5)
            y1 = 0
        elif anchor == 'left':
            x1 = 0
            y1 = int(center[1] - height * 0.5)
        elif anchor == 'right':
            x1 = w - width
            y1 = int(center[1] - height * 0.5)
        elif anchor == 'bottom':
            x1 = int(center[0] - width * 0.5)
            y1 = h - height
        else:
            raise ValueError('Unsupported anchor `{0}`'.format(anchor))

        x2 = x1 + width
        y2 = y1 + height

        return x1, y1, x2, y2


class CropProcessor(BaseProcessor):
    """
    Processor for cropping images either by percentage or absolute
    pixel amounts.

    Parameters
    ----------
    crop_box : list, tuple
        PIL compatible crop box relative to edges (not absolute to origin)
        by how much the image should be cropped - ``(x1, y1, x2, y2)``
    crop_percent : bool, optional
        If the crop box is given as percent or pixel values.
        Default is ``True``.
    """
    DEFAULTS = {
        'crop_box': None,
        'crop_percent': True,
    }

    def get_crop_box(self):
        if self.options.crop_box:
            crop_box = self.options.crop_box[:]
        else:
            crop_box = [None] * 4

        # make sure all values are provided
        for i, v in enumerate(crop_box):
            if v is None:
                crop_box[i] = 0

        # convert to pixel coordinates from origin
        if self.options.crop_percent:
            crop_box = [
                crop_box[0] / 100. * self.input_width,
                crop_box[1] / 100. * self.input_height,
                self.input_width - crop_box[2] / 100. * self.input_width,
                self.input_height - crop_box[3] / 100. * self.input_height,
            ]
        else:
            crop_box = [
                crop_box[0],
                crop_box[1],
                self.input_width - crop_box[2],
                self.input_height - crop_box[3],
            ]

        crop_box = map(int, crop_box)

        return crop_box

    def process(self, image):
        return image.crop(self.get_crop_box())


class FlipProcessor(BaseProcessor):
    """
    Processor for flipping the image around horizontal or vertical axis.

    Parameters
    ----------
    flip : str
        Flip mode. If empty string, image is not flipped.

        :``x``: flipped around horizontal axis (upside-down)
        :``y``: flipped around vertical axis (left-right)
    """
    DEFAULTS = {
        'flip': '',
    }

    def process(self, image):
        if not self.options.flip:
            return image
        if self.options.flip in ['x', 'h']:
            method = Image.FLIP_LEFT_RIGHT
        else:
            method = Image.FLIP_TOP_BOTTOM
        return image.transpose(method)


class ResizeProcessor(AnchorCropProcessorMixin, BaseProcessor):
    """
    Processor for resizing images.

    Parameters
    ----------
    width : int
        Maximum width in pixels of resulting image
    height : int
        Maximum height in pixels of resulting image
    fit : str, optional
        If the aspect ratios of input and resize bounding box
        are not the same, how to fit the input image to the bbox.
        Default is ``fit``.

        :``fit``:
            Resize so that the longest image size is at most
            the size of the bbox while preserving aspect ratio.
        :``crop``, ``center``, ``fill``:
            Crop the image around center to fill the bbox.
        :``top``:
            Crop around top to fill the bbox.
        :``left``:
            Crop around left to fill the bbox.
        :``right``:
            Crop around right to fill the bbox.
        :``bottom``:
            Crop around bottom to fill the bbox.
    upscale : bool, optional
        If the bbox is larger than original image, whether to
        allow to upscale the image. Default is ``False``.
    """

    DEFAULTS = {
        'width': None,
        'height': None,
        'fit': 'fit',
        'upscale': False,
    }

    def prep(self, image, options):
        super(ResizeProcessor, self).prep(image, options)
        self.options.width = self.options.width or self.input_width
        self.options.height = self.options.height or self.input_height

    def get_scaled_size(self):
        """
        Get the size of image to be resized to. If the fit mode is not ``fit``,
        the size could be bigger than bounding box however the image
        will eventually be cropped to match the bbox size.
        """
        width, height = map(float, self.input_size)
        box_width, box_height = map(float, (self.options.width, self.options.height))

        aspect_ratio = width / height

        # upscale if necessary
        if self.options.upscale:
            if width < box_width:
                width = box_width
                height = width / aspect_ratio
            if height < box_height:
                height = box_height
                width = height * aspect_ratio

        # fit into bounding box
        if width > box_width:
            height = int(max(height * box_width / width, 1))
            width = int(box_width)
        if height > box_height:
            width = int(max(width * box_height / height, 1))
            height = int(box_height)

        # enlarge for cropping
        if self.options.fit != 'fit':
            if width < box_width:
                width = box_width
                height = width / aspect_ratio
            if height < box_height:
                height = box_height
                width = height * aspect_ratio

        size = width, height

        size = map(lambda x: int(math.ceil(x)), size)
        return size

    def process(self, image):
        image = image.resize(self.get_scaled_size(), Image.ANTIALIAS)
        if self.options.fit != 'fit':
            image = image.crop(self.get_crop_box(image,
                                                 self.options.width,
                                                 self.options.height,
                                                 self.options.fit))
        return image


class RotateProcessor(BaseProcessor):
    """
    Processor for rotating the image by given amount of degrees.

    Parameters
    ----------
    degrees : int
        Degrees by how much rotate the image
    extend : bool, optional
        If ``True``, rotated image is extended to
        avoid cropping of the original image.
    color : list, tuple, optional
        RGBA color to fill the background for extended images.
        If ``None``, default PIL action is applied.
    preserve_transparency : bool, optional
        If the filled color is transparent and the original
        color mode was not ``'RGBA'``, whether to preserve the ``RGBA``
        or convert back to the original color space.
        Default is ``True``.
    """
    DEFAULTS = {
        'degrees': 0,
        'extend': True,
        'color': None,
        'preserve_transparency': True
    }

    def prep(self, image, options):
        super(RotateProcessor, self).prep(image, options)
        self.options.degrees = self.options.degrees
        # can be transposed instead of using rotation matrix
        self.options.transposable = self.options.degrees % 90 == 0

    def process(self, image):
        if self.options.transposable:
            if self.options.degrees == 0:
                return image
            method = getattr(Image, 'ROTATE_{0}'.format(self.options.degrees))
            return image.transpose(method)

        if self.options.color:
            original_mode = image.mode
            image = image.convert('RGBA')
            rotated = image.rotate(self.options.degrees,
                                   Image.BICUBIC,
                                   self.options.extend)
            background = Image.new('RGBA',
                                   rotated.size,
                                   color=self.options.color)
            image = Image.composite(rotated, background, rotated)

            if not self.options.preserve_transparency or self.options.color[3] == 255:
                image = image.convert(original_mode)

        else:
            image = image.rotate(self.options.degrees,
                                 Image.BICUBIC,
                                 self.options.extend)

        return image


class RotateCropProcessor(AnchorCropProcessorMixin, RotateProcessor):
    """
    Processor for rotating the image by given amount of degrees
    and then cropping it to avoid any non-image regions.

    Note that same parameters as for ``RotateProcessor`` can be
    provided except ``extend`` and ``color`` parameters.

    Parameters
    ----------
    crop_mode : str, optional
        Mode of how the image should be cropped to avoid non-image
        regions. Default is ``aspect_ratio``.

        :``aspect_ratio``:
            Maximum crop while preserving original image aspect ratio
        :``max_area``:
            Maximum crop where the cropped image will be of max area.

    """
    DEFAULTS = dict(RotateProcessor.DEFAULTS)
    DEFAULTS.update({
        'crop_mode': 'aspect_ratio',
    })

    def prep(self, image, options):
        super(RotateCropProcessor, self).prep(image, options)
        self.options.extend = True
        self.options.color = None

    def get_rotated_rect_aspect_ratio(self, rotated):
        """
        Get size of cropped image while maintaining original aspect ratio.
        """
        aspect_ratio = float(self.input_width) / self.input_height
        rotated_aspect_ratio = float(rotated.size[0]) / rotated.size[1]
        angle = math.fabs(self.options.degrees) * math.pi / 180

        if aspect_ratio < 1:
            total_height = float(self.input_width) / rotated_aspect_ratio
        else:
            total_height = float(self.input_height)

        h = total_height / (aspect_ratio * math.sin(angle) + math.cos(angle))
        w = h * aspect_ratio

        return map(int, (w, h))

    def get_rotated_rect_max_area(self, rotated):
        """
        Get size of cropped image which makes sure the result is of maximum area.
        """
        # from http://stackoverflow.com/questions/16702966/rotate-image-and-crop-out-black-borders
        if self.input_width <= 0 or self.input_height <= 0:
            return 0, 0

        angle = self.options.degrees * math.pi / 180
        width_is_longer = self.input_width >= self.input_height
        if width_is_longer:
            side_long, side_short = self.input_size
        else:
            side_long, side_short = self.input_size[::-1]

        # since the solutions for angle, -angle and 180-angle are all the same,
        # if suffices to look at the first quadrant and the absolute values of sin,cos:
        sin_a, cos_a = abs(math.sin(angle)), abs(math.cos(angle))

        # half constrained case: two crop corners touch the longer side,
        # the other two corners are on the mid-line parallel to the longer line
        if side_short <= 2. * sin_a * cos_a * side_long:
            x = 0.5 * side_short
            wr, hr = (x / sin_a, x / cos_a) if width_is_longer else (x / cos_a, x / sin_a)

        # fully constrained case: crop touches all 4 sides
        else:
            cos_2a = cos_a * cos_a - sin_a * sin_a
            wr, hr = ((self.input_width * cos_a - self.input_height * sin_a) / cos_2a,
                      (self.input_height * cos_a - self.input_width * sin_a) / cos_2a)

        return map(int, (wr, hr))

    def process(self, image):
        rotated = super(RotateCropProcessor, self).process(image)

        if self.options.transposable:
            return rotated

        w, h = getattr(self, 'get_rotated_rect_{0}'
                             ''.format(self.options.crop_mode))(rotated)
        crop_box = self.get_crop_box(rotated, w, h)

        return rotated.crop(crop_box)


crop_processor = CropProcessor.as_callable()
flip_processor = FlipProcessor.as_callable()
resize_processor = ResizeProcessor.as_callable()
rotate_processor = RotateProcessor.as_callable()
rotate_crop_processor = RotateCropProcessor.as_callable()
