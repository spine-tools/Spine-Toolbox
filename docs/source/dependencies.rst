.. Spine Toolbox Dependencies
   Created 17.1.2019

************
Dependencies
************

Spine Toolbox requires Python 3.7 or Python 3.8. Python 3.9 is not supported yet.

The dependencies have been split to required packages and development packages. The required packages
must be installed for the application to start. The development packages contain tools that are
recommended for developers. If you want to deploy the application yourself by using the provided
*cx_Freeze_setup.py* file, you need to install the *cx_Freeze* package (v6.3 or newer recommended).
All version numbers are minimum versions except for PySide2, where the version should be 5.14.
PySide2 version 5.15 is allowed but not fully supported (yet). Version x.x means that the newest
version available is recommended.

Required packages
-----------------

At the moment, Spine Toolbox consists of four main packages (*spinetoolbox*, *spine-engine*, *spine-items*,
and *spinedb_api*) developed in Spine project. Below is a list of packages that will
be installed when the app is installed using the recommended `pip install requirements.txt`
command.

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| pyside2           | 5.14          |     LGPL      |
+-------------------+---------------+---------------+
| datapackage       | 1.15          |     MIT       |
+-------------------+---------------+---------------+
| jupyter-client    | 6.1           |     BSD       |
+-------------------+---------------+---------------+
| qtconsole         | 4.3.1         |     BSD       |
+-------------------+---------------+---------------+
| sqlalchemy        | 1.3.17        |     MIT       |
+-------------------+---------------+---------------+
| spinedb_api       | x.x           |     LGPL      |
+-------------------+---------------+---------------+
| spine_engine      | x.x           |     LGPL      |
+-------------------+---------------+---------------+
| spine_items       | x.x           |     LGPL      |
+-------------------+---------------+---------------+
| openpyxl          | 3.0           |   MIT/Expat   |
+-------------------+---------------+---------------+
| numpy             | 1.15.1        |     BSD       |
+-------------------+---------------+---------------+
| matplotlib        | 3.0           |     BSD       |
+-------------------+---------------+---------------+
| scipy             | 1.1.0         |     BSD       |
+-------------------+---------------+---------------+
| networkx          | 2.2           |     BSD       |
+-------------------+---------------+---------------+
| pymysql           | 0.9.2         |     MIT       |
+-------------------+---------------+---------------+
| pyodbc            | 4.0.23        |     MIT       |
+-------------------+---------------+---------------+
| psycopg2          | 2.7.4         |     LGPL      |
+-------------------+---------------+---------------+
| cx_Oracle         | 6.3.1         |     BSD       |
+-------------------+---------------+---------------+
| python-dateutil   | 2.8.1         |     PSF       |
+-------------------+---------------+---------------+
| pandas            | 0.24.0        |     BSD       |
+-------------------+---------------+---------------+
| jsonschema        | 2.6           |     MIT       |
+-------------------+---------------+---------------+
| gdx2py            | 2.0.4         |     MIT       |
+-------------------+---------------+---------------+
| jill              | 0.8.1         |     MIT       |
+-------------------+---------------+---------------+
| alembic           | 1.5.4         |     MIT       |
+-------------------+---------------+---------------+
| faker             | 6.1.1         |     MIT       |
+-------------------+---------------+---------------+
| ijson             | 2.6.1         |     BSD       |
+-------------------+---------------+---------------+
| dagster           | 0.9.15        |  Apache-2.0   |
+-------------------+---------------+---------------+


Development packages
^^^^^^^^^^^^^^^^^^^^

Below is a list of development packages (installed when running `pip install dev-requirements.txt`
command). Sphinx and sphinx_rtd_theme packages are needed for building the user guide. Black is used
for code formatting while pylint does linting. Pre-commit hook enables automatic code formatting at
git commit.

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| black             | ==19.3b0      |     MIT       |
+-------------------+---------------+---------------+
| pre-commit        | ==2.0.1       |     MIT       |
+-------------------+---------------+---------------+
| pyYAML            | <5            |     GPL       |
+-------------------+---------------+---------------+
| pylint            | >=2.3.0       |     GPL       |
+-------------------+---------------+---------------+
| sphinx            | >=1.7.5       |     BSD       |
+-------------------+---------------+---------------+
| sphinx_rtd_theme  | >=0.4.0       |     MIT       |
+-------------------+---------------+---------------+
| recommonmark      | >=0.5.0       |     MIT       |
+-------------------+---------------+---------------+
| sphinx-autoapi    | >=1.1.0       |     MIT       |
+-------------------+---------------+---------------+
