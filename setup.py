""" Setup script for prosumpy"""

import codecs
from setuptools import setup, find_packages
import os

# import distutils.command.bdist_conda

import prosumpy

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

version = prosumpy.__version__

requirements = ['numpy>=1.10',
                'matplotlib>=1.5.1',
                'pandas>=0.18']

setup(
    name="prosumpy",
    author="Sylvain Quoilin, Konstantinos Kavvadias",
    author_email="kavvkon@gmail.com",
    url='https://github.com/energy-modelling-toolkit/prosumpy',
    description='Energy prosumer analysis with Python',
    long_description=read('README.md'),
    license="EUPL v1.1.",
    version=version,
    install_requires=requirements,
    keywords=['prosumer', 'energy', 'photovoltaics', 'self-consumption', 'simulation'],
    packages=find_packages(),
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Natural Language :: English',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

    ],

)
