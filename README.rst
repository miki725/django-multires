Django-Multires
===============

.. image:: https://d2weczhvl823v0.cloudfront.net/miki725/django-multires/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

Django-multires is a plug-and-play Django app for managing multiple image resolutions in a db-driven approach.

Why another lib
---------------

Images are important aspect of web development. However they come at a price of extra bandwidth due to their size which especially becomes important on mobile devices. To handle this, some sites generate multiple resolutions of each image to serve to different devices or network conditions. The usual approach in doing so is to define ahead of time terms for different levels of resolutions which will be available. For example a ``thumbnail`` could be an image up to ``200x200``, ``high-res`` be up to ``2500x2500``, etc. This is what most of the current image-management Django apps do such as `easy-thumbnails <https://github.com/SmileyChris/easy-thumbnails>`_. In case of ``easy_thumbnails``, these presets are called aliases and some of them even allow to define more advanced options such as crop, rotation, etc. This allows for some advanced uses such as if need to generate image gallery thumbnails cropped square. That is until in one of images a face will be cropped out due to the fact that original image and gallery thumbnails are not of the same aspect ratio hence some regions need to be cropped. This results in adding a field to a model for square thumbnail image. Then of course you need the same image for the landing page banner which should be of 16x9 aspect ratio. That again cropps the image in unpleasing fashion so you end up adding another field. You can probably see where this is going.

This library does not require to hard code any rules as to how the images will be processed. All rules are stored in a database. So if a need arises to apply a special treatment to any specific image, it is just a matter of creating another rule in db on how to process that specific image. Additional advantage of this approach is that it becomes much easier to change these rules once the application is deployed (no need to change anything in ``settings.py``).

Overview
--------

As discussed in **Why another lib**, this library approaches a problem of managing multiple image resolutions in more database-driven way. Each rule how the image should be processed is represented by a ``MultiresRecipe`` model and each processed image is represented by ``MultiresImage`` model. Using them directly can be tedious  however you can use a lightweight wrapper ``MultiresImageField`` around ``ImageField`` for more simple API::

    from multires import MultiresImageField, MultiresRecipe

    # a simple thumbnails recipe
    # usually would create this in Django admin
    recipe = MultiresRecipe.objects.get_or_create(
        title='thumbnail',
        description='Recipe for thumbnails',
        namespace='abc',
        width=200, height=200,
        file_type='jpeg', quality=80
    )[0]

    # some test data
    class FooModel(models.Model):
        image = MultiresImageField(upload_to='foo', namespace='abc')
    foo = FooModel.objects.create(image=...)

    # get multires image for foo's image
    image = foo.image.get_multires_image(recipe)

    # get lazy url for thumbnail image
    print(image.image.url)

    # or process it manually
    image.process()

    # get the url for the processed image as per MEDIA_URL
    # since image has been already processed
    print(image.image.url)

Installation
------------

Since this package is still in development, no stable version has been uploaded to PYPI yet. You can however install it as a `developer <http://github.com/miki725/django-multires/archive/develop.tar.gz#egg=django_multires-dev>`_ version::

    $ pip install django-multires==dev

Once installed, add it to the ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...,
        'multires',
        ...
    )

And then do the syncdb to create the necessary db tables::

    $ python manage.py syncdb

Add the multires urls to Django's root urls config to enable lazy urls::

    urlpatterns = patterns(
        ...
        url(r'^multires/', include('multires.urls', namespace='multires')),
    )

Credits
-------

Current maintainers:

* Miroslav Shubernetskiy - `GitHub <http://bit.ly/mkgithub>`_

