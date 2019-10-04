######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from spinetoolbox.config import REQUIRED_SPINEDB_API_VERSION, SPINE_TOOLBOX_VERSION

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as requirements_file:
    requirements = [line.strip() for line in requirements_file.readlines()]

# Replace the git link to spinedb_api by the package's real name
for index, requirement in enumerate(requirements):
    if requirement == "git+https://github.com/Spine-project/Spine-Database-API.git#egg=spinedb_api":
        requirements[index] = "spinedb_api == {}".format(REQUIRED_SPINEDB_API_VERSION)
        break

setup(
    name="Spine-Toolbox",
    version=SPINE_TOOLBOX_VERSION,
    description="An application to define, manage, and execute various energy system simulation models",
    long_description=readme,
    author="Spine Project consortium",
    author_email='spine_info@vtt.fi',
    url='https://github.com/Spine-project/Spine-Toolbox',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'spinetoolbox=spinetoolbox.main:main'
        ]
    },
    include_package_data=True,
    license="LGPL-3.0-or-later",
    zip_safe=False,
    keywords='',
    classifiers=[
    ],
    install_requires=requirements,
    test_suite='test',
)
