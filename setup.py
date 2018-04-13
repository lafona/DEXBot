#!/usr/bin/env python

from setuptools import setup
from setuptools.command.install import install
from distutils.util import convert_path


main_ns = {}
ver_path = convert_path('dexbot/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)
    VERSION = main_ns['__version__']


setup(
    name='dexbot',
    version=VERSION,
    description='Trading bot for the DEX (BitShares)',
    long_description=open('README.md').read(),
    author='Ian Haywood',
    author_email='ihaywood3@gmail.com',
    maintainer='Ian Haywood',
    maintainer_email='',
    url='http://www.github.com/ihaywood3/dexbot',
    keywords=['DEX', 'bot', 'trading', 'api', 'blockchain'],
    packages=[
        "dexbot",
        "dexbot.strategies",
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'dexbot = dexbot.cli:main',
        ],
    },
    install_requires=[
        "bitshares>=0.1.11",
        "uptick>=0.1.4",
        "click",
        "sqlalchemy",
        "appdirs",
        #"pyqt5",
        "sdnotify",
        "matplotlib",
        #'pyqt-distutils',
        "ruamel.yaml>=0.15.37"
    ],
    include_package_data=True,
)
