import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='Evolution',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    license='???',
    description='A simple system for data-based contests.',
    long_description='README.rst',
    url='http://qed.ai',
    author='Stanisław Barzowski',
    author_email='stanislaw.barzowski@gmail.com',
    install_requires=[
        'django>=1.9.3,<1.10',
        'django-downloadview>=1.8',
        'django-debug-toolbar>=1.4',
        'Markdown>=2.6.5',
        'py-gfm>=0.1.1',
        'Pygments>=2.1.1',
        'bleach>=1.4.2',
        'pytz',
        'uwsgi>=2.0.12',
        'psycopg2>=2.6.1',
        'django-webtest>=1.7.8',
        'django-allauth>=0.25.2',
    ]
)
