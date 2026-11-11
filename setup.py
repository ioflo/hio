#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
$ python setup.py register sdist upload

First Time register project on pypi
https://pypi.org/manage/projects/


More secure to use twine to upload
$ pip3 install twine
$ python setup.py sdist
$ twine upload dist/hio-0.7.5.tar.gz


Update sphinx /docs
$ cd /docs

$ sphinx-build -b html source build/html
or
$ sphinx-apidoc -f -o source/ ../src/
$ make html

$ git tag # lists all tags
$ git tag -a v0.6.11 -m "new feature"
$ git show v0.6.11
$ git push --tags # pushes tags to default remote
$ git push ioflo --tags   # pushes tags to ioflo remote


Best practices for setup.py and requirements.txt
https://caremad.io/posts/2013/07/setup-vs-requirement/
"""


from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup



setup(
    name='hio',
    version='0.7.21',  #  also change in src/hio/__init__.py
    license='Apache Software License 2.0',
    description='Hierarchical Concurrency with Async IO',
    long_description=("HIO Hierarchical Concurrency and Asynchronous IO Library. "
                      "Rich structured contextual concurrrent coroutines with"
                      " asynchrounous IO modules."),
    author='Samuel M. Smith',
    author_email='smith.samuel.m@gmail.com',
    url='https://github.com/ioflo/hio',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        # uncomment if you test on these interpreters:
        #'Programming Language :: Python :: Implementation :: PyPy',
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://hio.readthedocs.io/',
        'Changelog': 'https://hio.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/ProSapien/hio/issues',
    },
    keywords=[ "hierarchical concurrency",
               "async io",
               "rich contextual concurrency",
               "structured concurrency",
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires='>=3.14.0',
    install_requires=[
        'lmdb==2.3.0',
        'msgpack==1.2.2',
        'cbor2==6.1.4',
        'multidict==6.9.1',
        'falcon==4.3.1',
        'ordered-set==4.1.0',
        'sortedcontainers==2.4.0',
        'pysodium==0.7.18',
        'blake3==1.0.9',
    ],
    extras_require={
        #'test': [
            #'coverage==7.16.0',
            #'pytest==9.1.1',
            #'pytest-cov==7.1.0',
            #'pytest-shell==0.3.2',
            #'pytest-xdist==3.8.0',
        #],
    },
    tests_require=[
                    'coverage==7.16.0',
                    'pytest==9.1.1',
                    'pytest-cov==7.1.0',
                    'pytest-shell==0.3.2',
                    'pytest-xdist==3.8.0',
                  ],
    setup_requires=[
    ],
    entry_points={
        'console_scripts': [
            'hio = hio.cli:main',
            'hiod = hio.daemon:main'
        ]
    },
)
