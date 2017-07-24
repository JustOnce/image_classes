#!/usr/bin/env python
# coding: utf-8
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version('mommy_spatial_generators', '__init__.py')


if sys.argv[-1] == 'publish':
    try:
        import wheel
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()


if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()


# readme = open('README.md').read()
# history = open('HISTORY.md').read().replace('.. :changelog:', '')


setup(
    name='images_classes',
    version=version,
    description="""Helpers to work with images""",
    # long_description=readme + '\n\n' + history,
    long_description="",
    author='Denis Nikanorov',
    author_email='nikanorovdenis@yande.xru',
    url='https://github.com/JustOnce/image_classes',
    packages=[
        'image_classes',
    ],
    include_package_data=True,
    install_requires=[
    ],
    license="BSD",
    zip_safe=False,
    keywords='image_classes',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        # 'Framework :: Django :: 1.8',
        # 'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
    ],
)