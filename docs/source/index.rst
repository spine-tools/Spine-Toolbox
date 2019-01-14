.. Spine Toolbox documentation master file, created by
   sphinx-quickstart on Mon Jun 18 12:58:32 2018.

Welcome to Spine Toolbox's User Guide!
======================================
Spine Toolbox is an application, which provides means to define, manage, and execute complex data processing and
computation tasks, such as energy system models.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   settings
   getting_started
   terminology
   edit_view_spinedatabase
   data_import_export
   contribution_guide
   code_ref

Dependencies
------------
Spine Toolbox requires Python 3.5 or higher.

Spine Toolbox uses code from packages and/or projects listed in the table below. Required packages must be
installed for the application to start. Users can choose the SQL dialect API (pymysql, pyodbc psycopg2, and cx_Oracle)
they want to use. These can be installed in Spine Toolbox when needed. Sphinx, recommonmark, and cx_Freeze
packages are needed for building the user guide and for deploying the application. All version numbers are
minimum versions.

+-------------------+---------------+---------------+
| Package name      |    Version    |     License   |
+===================+===============+===============+
| **Required packages (requirements.txt)**          |
+-------------------+---------------+---------------+
| pyside2           | 5.6           |     LGPL      |
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
| cx_Freeze         | 6.0b1         | PSFL (deriv.) |
+-------------------+---------------+---------------+

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
