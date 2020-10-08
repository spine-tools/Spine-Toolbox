######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Setup script for Python's setuptools.

:author: A. Soininen (VTT)
:date:   3.10.2019
"""

from setuptools import setup, find_packages
from spinetoolbox.config import (
    REQUIRED_SPINEDB_API_VERSION,
    REQUIRED_SPINE_ENGINE_VERSION,
)

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

version = {}
with open("spinetoolbox/version.py") as fp:
    exec(fp.read(), version)

install_requires = [
    "pyside2 >=5.14, <5.15",
    "datapackage >= 1.15",
    "jupyter-client < 5.3.2",
    "qtconsole >= 4.3.1",
    "sqlalchemy >= 1.3",
    "spinedb_api >= {}".format(REQUIRED_SPINEDB_API_VERSION),
    "spine_engine >= {}".format(REQUIRED_SPINE_ENGINE_VERSION),
    "numpy >= 1.15.1",
    "matplotlib >= 3.0",
    "scipy >= 1.1.0",
    "networkx > 2.2",
    "cx_Oracle >= 6.3.1",
    "pandas >= 0.24.0",
]

setup(
    name="spinetoolbox",
    version=version["__version__"],
    description="An application to define, manage, and execute various energy system simulation models",
    long_description=readme,
    author="Spine Project consortium",
    author_email="spine_info@vtt.fi",
    url="https://github.com/Spine-project/Spine-Toolbox",
    packages=find_packages(exclude=("tests",)),
    entry_points={"console_scripts": ["spinetoolbox=spinetoolbox.main:main"]},
    include_package_data=True,
    license="LGPL-3.0-or-later",
    zip_safe=False,
    keywords="",
    classifiers=[],
    python_requires='>=3.6, <3.8',
    install_requires=install_requires,
    test_suite="tests",
)
