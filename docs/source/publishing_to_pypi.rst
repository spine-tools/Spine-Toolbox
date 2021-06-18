.. _Publising to PyPI:

Publising to PyPI
=================

This document describes the prerequisities and workflow to publish Spine Toolbox
(or any Python package) to `The Python Package Index (PyPI) <https://pypi.org>`_.
For a complete tutorial, see `Packaging Python Projects <https://packaging.python.org/tutorials/packaging-projects/>`_.

First, make sure you have all the developer packages installed by calling

::

    $ pip install --upgrade -r dev-requirements.txt

inside your Python environment.


Building 
--------

Build a source distribution archive and a wheel package with

::

    $ python setup.py sdist bdist_wheel

This will create distribution files under the ‘dist’ directory.


Uploading
---------

Before making a real upload, please test using TestPyPI which is a separate 
instance from the real index server.
Once a version has been uploaded to PyPI, it cannot be reverted or modified. 

`Register an an account <https://test.pypi.org/account/register/>`_ and ask 
some of the owners of `the Spine Toolbox package <https://test.pypi.org/project/spinetoolbox/>`_ 
(or other relevant package) to add you as a maintainer.

Upload the distribution using

::

    $ twine upload --repository testpypi dist/*

See `Using TestPyPI <https://packaging.python.org/guides/using-testpypi/>`_ 
for more information. To avoid entering your username and password every time,
see `Keyring support in twine documentation <https://twine.readthedocs.io/en/latest/#keyring-support>`_.

If everything went smoothly, you are ready to upload the the real index.
Again, you need to register to PyPI and ask to become a maintainer of the package
you want to upload to. Upload the distribution using

::

    $ twine upload dist/*
