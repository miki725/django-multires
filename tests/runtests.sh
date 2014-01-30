#!/bin/sh

export DJANGO_MANAGE=manage.py
export args="$@"

python $DJANGO_MANAGE test multires "$args"
