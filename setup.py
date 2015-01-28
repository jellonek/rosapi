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
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Systems Administration',
    ],
    author='Piotr Skamruk',
    author_email='piotr.skamruk@gmail.com',
    keywords='mikrotik routerboard ros api',
    packages=find_packages(),
    zip_safe=True,
)
