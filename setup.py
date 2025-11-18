# -*- coding:utf-8 -*-

import os
import sys
from distutils.core import setup
from setuptools import find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")
here = os.path.abspath(os.path.dirname(__file__))

setup_args = dict(
    name='nuxt',
    version='0.2.13',
    description='A integration framework for build web app.',
    long_description="Nuxt is a integration framework for build web app, built on top of [Madara](https://github.com/Arvintian/madara)/[Starlette](https://github.com/encode/starlette)/[Gunicorn](https://github.com/benoitc/gunicorn)/[Uvicorn](https://github.com/encode/uvicorn).",
    long_description_content_type="text/markdown",
    author='arvin',
    license='MIT',
    url='https://github.com/Arvintian/nuxt',
    author_email='arvintian8@gamil.com',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
    [console_scripts]
    nuxt=nuxt.__main__:run
    ''',
)

if 'setuptools' in sys.modules:
    setup_args['zip_safe'] = False
    setup_args['install_requires'] = install_requires = []

    with open('requirements.txt', "r", encoding="utf-8") as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith('#') or '://' in req:
                continue
            install_requires.append(req)


def main():
    setup(**setup_args)


if __name__ == "__main__":
    main()
