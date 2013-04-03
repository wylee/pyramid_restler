from setuptools import setup, find_packages


version = open('version.txt').read().strip()


setup(
    name='pyramid_restler',
    version=version,
    description='RESTful views for Pyramid',
    author='Wyatt Lee Baldwin',
    author_email='wyatt.lee.baldwin@gmail.com',
    keywords='Web REST Pylons Pyramid',
    url='https://bitbucket.org/wyatt/pyramid_restler',
    install_requires=(
        'pyramid>=1.3',
    ),
    extras_require=dict(
        dev=(
            'coverage>=3.5.2',
            'repoze.sphinx.autointerface>=0.6.2',
            'Sphinx>=1.1.3',
            'SQLAlchemy>=0.8.0',
            'psycopg2>=2.4.6',
            'waitress>=0.8.1',
        ),
    ),
    packages=find_packages(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Framework :: Pylons',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
