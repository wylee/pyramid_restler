from setuptools import setup, find_packages


setup(
    name='pyramid_restler',
    version='0.1dev',
    description='RESTful views for Pyramid',
    author='Wyatt Lee Baldwin',
    author_email='wyatt.lee.baldwin@gmail.com',
    install_requires=(
        'pyramid>=1.0',
    ),
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Pylons',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
