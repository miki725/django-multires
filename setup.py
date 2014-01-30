import os
from setuptools import setup
from multires import __version__, __author__


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])

    if filepaths:
        return {package: filepaths}
    else:
        return None


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-multires',
    version=__version__,
    author=__author__,
    author_email='miroslav@miki725.com',
    description=('Django-multires is a plug-and-play Django app for '
                 'managing multiple image resolutions in a db-driven approach.'),
    long_description=read('README.rst') + read('LICENSE.rst'),
    url='https://github.com/miki725/django-multires',
    license='MIT',
    keywords='django',
    packages=get_packages('multires'),
    data_files=get_package_data('multires'),
    install_requires=[
        'django',
        'django-auxilium==dev',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
    ],
)
