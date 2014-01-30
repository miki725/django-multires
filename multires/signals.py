from __future__ import unicode_literals, print_function
from django.dispatch import Signal


multires_source_created = Signal(providing_args=['instance', 'field_name'])
