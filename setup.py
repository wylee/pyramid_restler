from setuptools import setup, find_packages


version = open('version.txt').read().strip()


setup(
    name='pyramid_restler',
    version=version,
    description='RESTful views for Pyramid',
    author='Wyatt Baldwin',
    author_email='wyatt.lee.baldwin@gmail.com',
    keywords='Web REST Pylons Pyramid',
    url='https://github.com/wylee/pyramid_restler',
    install_requires=(
        'pyramid>=1.3',
    ),
    extras_require=dict(
        dev=(
            'coverage>=4.1',
            'repoze.sphinx.autointerface>=0.8',
            'Sphinx>=1.4.1',
            'SQLAlchemy>=1.0.13',
            'psycopg2>=2.6.1',
            'waitress>=0.9.0',
        ),
    ),
    packages=find_packages(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ),
)
