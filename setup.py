import sys
from setuptools import setup, find_packages


with open('pyramid_restler/__init__.py') as fp:
    for line in fp:
        if line.startswith('__version__'):
            version = line.split('=', 1)[1].strip()[1:-1]

install_requires = [
    'pyramid',
]

if sys.version_info < (3, 7):
    install_requires.append('dataclasses')

setup(
    name='pyramid_restler',
    version=version,
    description='RESTful views & resources for Pyramid',
    author='Wyatt Baldwin',
    author_email='self@wyattbaldwin.com',
    keywords='Web REST resource Pylons Pyramid',
    url='https://gitlab.com/wylee/pyramid_restler',
    install_requires=install_requires,
    extras_require=dict(
        dev=[
            'coverage',
            'flake8',
            'psycopg2-binary',
            'repoze.sphinx.autointerface',
            'Sphinx',
            'SQLAlchemy',
            'tox',
            'waitress',
        ],
    ),
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
