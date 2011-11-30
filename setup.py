from setuptools import setup, find_packages


version = open('version.txt').read().strip()


setup(
    name='pyramid_restler',
    version=version,
    description='RESTful views for Pyramid',
    author='Wyatt Lee Baldwin',
    author_email='wyatt.lee.baldwin@gmail.com',
    keywords='Web REST Pylons Pyramid',
    install_requires=(
        'pyramid>=1.2.3',
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
