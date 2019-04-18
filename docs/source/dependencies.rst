.. Spine Toolbox Dependencies
   Created 17.1.2019

************
Dependencies
************

Spine Toolbox requires Python 3.5 or higher.

Spine Toolbox uses code from packages and/or projects listed in the table below. Required packages
must be installed for the application to start. Users can choose the SQL dialect API (pymysql,
pyodbc psycopg2, and cx_Oracle) they want to use. These can be installed in Spine Toolbox when
needed. Sphinx, sphinx_rtd_theme, and recommonmark packages are needed for building the user guide.
If you want to deploy the application by using the provided *setup.py* file, you need to install
*cx_Freeze* package (6.0b1 version or newer is recommended). All version numbers are minimum
versions except pyside2 5.12 version is not supported (yet).

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| **Required packages (requirements.txt)**          |
+-------------------+---------------+---------------+
| pyside2           | <5.12         |     LGPL      |
+-------------------+---------------+---------------+
| datapackage       | 1.2.3         |     MIT       |
+-------------------+---------------+---------------+
| qtconsole         | 4.3.1         |     BSD       |
+-------------------+---------------+---------------+
| sqlalchemy        | 1.2.6         |     MIT       |
+-------------------+---------------+---------------+
| openpyxl          | 2.4.0         |   MIT/Expat   |
+-------------------+---------------+---------------+
| spinedatabase_api | 0.0.1         |     LGPL      |
+-------------------+---------------+---------------+
| numpy             | 1.15.1        |    BSD        |
+-------------------+---------------+---------------+
| matplotlib        | 2.2.3         |    BSD        |
+-------------------+---------------+---------------+
| scipy             | 1.1.0         |    BSD        |
+-------------------+---------------+---------------+
| networkx          | 2.2           |    BSD        |
+-------------------+---------------+---------------+
| **Optional packages (optional-requirements.txt)** |
+-------------------+---------------+---------------+
| pymysql           | 0.9.2         |     MIT       |
+-------------------+---------------+---------------+
| pyodbc            | 4.0.23        |     MIT       |
+-------------------+---------------+---------------+
| psycopg2          | 2.7.4         |     LGPL      |
+-------------------+---------------+---------------+
| cx_Oracle         | 6.3.1         |     BSD       |
+-------------------+---------------+---------------+
| sphinx            | 1.7.5         |     BSD       |
+-------------------+---------------+---------------+
| sphinx_rtd_theme  | 0.4.0         |     MIT       |
+-------------------+---------------+---------------+
| recommonmark      | 0.4.0         |     MIT       |
+-------------------+---------------+---------------+
