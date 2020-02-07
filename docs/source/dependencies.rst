.. Spine Toolbox Dependencies
   Created 17.1.2019

************
Dependencies
************

Spine Toolbox requires Python 3.6 or Python 3.7. Python 3.8 is not supported yet.

Spine Toolbox uses code from packages and/or projects listed in the table below. Required packages
must be installed for the application to start. Users can choose the SQL dialect API (pymysql,
pyodbc psycopg2, and cx_Oracle) they want to use. These can be installed in Spine Toolbox when
needed. If you want to deploy the application by using the provided *setup.py* file,
you need to install *cx_Freeze* package (6.0b1 version or newer is recommended).
All version numbers are minimum versions except for pyside2, where the version should be less
than 5.12, which is not supported (yet).

Required packages
-----------------

The following packages are available from ``requirements.txt``

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| pyside2           | <5.12         |     LGPL      |
+-------------------+---------------+---------------+
| datapackage       | 1.2.3         |     MIT       |
+-------------------+---------------+---------------+
| qtconsole         | 4.3.1         |     BSD       |
+-------------------+---------------+---------------+
| sqlalchemy        | 1.2.6         |     MIT       |
+-------------------+---------------+---------------+
| openpyxl          | 2.5.0         |   MIT/Expat   |
+-------------------+---------------+---------------+
| spinedb_api       | 0.0.36        |     LGPL      |
+-------------------+---------------+---------------+
| numpy             | 1.15.1        |    BSD        |
+-------------------+---------------+---------------+
| matplotlib        | 3.0           |    BSD        |
+-------------------+---------------+---------------+
| scipy             | 1.1.0         |    BSD        |
+-------------------+---------------+---------------+
| jupyter-client    | 5.2.4         |    BSD        |
+-------------------+---------------+---------------+
| networkx          | 2.2           |    BSD        |
+-------------------+---------------+---------------+
| pymysql           | 0.9.2         |     MIT       |
+-------------------+---------------+---------------+
| pyodbc            | 4.0.23        |     MIT       |
+-------------------+---------------+---------------+
| psycopg2          | 2.7.4         |     LGPL      |
+-------------------+---------------+---------------+
| cx_Oracle         | 6.3.1         |     BSD       |
+-------------------+---------------+---------------+
| python-dateutil   | 2.8.0         |     PSF       |
+-------------------+---------------+---------------+
| pandas            | 0.24.0        |     BSD       |
+-------------------+---------------+---------------+

Developer packages
^^^^^^^^^^^^^^^^^^

The developer packages are available from ``dev-requirements.txt``.
Sphinx and sphinx_rtd_theme packages are needed for building the user guide.
Black is used for code formatting while pylint does linting.
Pre-commit hook enables automatic code formatting at git commit.

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| black             | 19.3b0        |     MIT       |
+-------------------+---------------+---------------+
| pre-commit        | 1.16.1        |     MIT       |
+-------------------+---------------+---------------+
| pylint            | 2.3.0         |     GPL       |
+-------------------+---------------+---------------+
| sphinx            | 1.7.5         |     BSD       |
+-------------------+---------------+---------------+
| sphinx_rtd_theme  | 0.4.0         |     MIT       |
+-------------------+---------------+---------------+
| recommonmark      | 0.5.0         |     MIT       |
+-------------------+---------------+---------------+
| sphinx-autoapi    | 1.1.0         |     MIT       |
+-------------------+---------------+---------------+
