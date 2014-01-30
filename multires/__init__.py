from __future__ import unicode_literals, print_function

__author__ = 'Miroslav Shubernetskiy'
__version__ = '0.1'

try:
    from .models import MultiresRecipe, MultiresImage
    from .fields import MultiresImageField
except Exception:
    pass
