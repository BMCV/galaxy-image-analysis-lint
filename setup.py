#!/usr/bin/env python

from setuptools import setup

version = dict()
with open('gialint/version.py') as f:
    exec(f.read(), version)


setup(
    name='gialint',
    version=version['__version__'],
    description='Linter for tool wrappers in Galaxy Image Analysis',
    author='Leonid Kostrykin',
    author_email='leonid.kostrykin@bioquant.uni-heidelberg.de',
    url='https://kostrykin.com',
    license='MIT',
    packages=['gialint', 'gialint._checks'],
    python_requires='>=3.10',
    install_requires=[
        'galaxy-util>=25.0',
        'lxml>=6.0.2',
        'Cheetah3>=3.2.6.post1',
    ],
)
