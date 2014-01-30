from __future__ import unicode_literals, print_function
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from vanilla.model_views import GenericModelView
from .models import MultiresImage


class LazyMultiresImage(GenericModelView):
    """
    Lazy processing of multires images.
    When accessing a not processed multires image
    via this view, first it processed it and then
    redirects to the actual image url.
    """
    model = MultiresImage
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        image = self.get_object()
        if not image.image:
            image.process(save=True)
        return HttpResponseRedirect(image.image.url)
