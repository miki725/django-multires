from __future__ import unicode_literals, print_function
from django.contrib.admin import site
from .models import *


for model in [MultiresRecipe,
              MultiresImage]:
    site.register(model)
