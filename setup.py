import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as file:
    README = file.read()
with open(os.path.join(here, 'VERSION.txt')) as file:
    VERSION = file.readline().strip()

setup(
    name='rosapi',
    version=VERSION,
    description='Routerboard API',
    long_description=README,
    url='https://github.com/jellonek/rosapi',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Systems Administration',
    ],
    author='Piotr Skamruk',
    author_email='piotr.skamruk@gmail.com',
    keywords='mikrotik routerboard ros api',
    packages=find_packages(),
    zip_safe=True,
)
