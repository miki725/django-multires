#!/usr/bin/env python
"""
The ``manage.py`` is for some IDEs which require manage.py
to run tests directly within the IDE.
"""
from __future__ import unicode_literals, print_function
import os
import sys

# make app importable
sys.path.append(os.path.abspath(os.path.join(__file__, '..', '..')))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
