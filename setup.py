######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from spinetoolbox.version import __version__
from spinetoolbox.config import REQUIRED_SPINEDB_API_VERSION, REQUIRED_SPINE_ENGINE_VERSION

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

install_requires = [
    "pyside2 >=5.14, <5.15",
    "datapackage >= 1.15.2",
    "jupyter-client >= 6.1.12",
    "qtconsole >= 5.0.3",
    "sqlalchemy >=1.3, <1.4",
    "spinedb_api >= {}".format(REQUIRED_SPINEDB_API_VERSION),
    "spine_engine >= {}".format(REQUIRED_SPINE_ENGINE_VERSION),
    "numpy >= 1.20.2",
    "matplotlib!=3.2.1, >3.0, <3.3.1",
    "scipy >= 1.6.3",
    "networkx >= 2.5.1",
    "cx-Oracle >= 8.1.0",
    "pandas >= 1.2.4",
    "pymysql >= 1.0.2",
    "pyodbc >= 4.0.30",
    "psycopg2 >= 2.8.6",
    "jill >= 0.9.2",
]

setup(
    name="spinetoolbox",
    version=__version__,
    description="An application to define, manage, and execute various energy system simulation models",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Spine Project consortium",
    author_email="spine_info@vtt.fi",
    url="https://github.com/Spine-project/Spine-Toolbox",
    packages=find_packages(exclude=("tests*", "execution_tests*")),
    entry_points={"console_scripts": ["spinetoolbox=spinetoolbox.main:main"]},
    include_package_data=True,
    license="LGPL-3.0-or-later",
    zip_safe=False,
    keywords="",
    python_requires=">=3.6, <3.9",
    install_requires=install_requires,
    test_suite="tests",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/Spine-project/Spine-Toolbox/issues",
        "Documentation": "https://spine-toolbox.readthedocs.io",
    },
)
