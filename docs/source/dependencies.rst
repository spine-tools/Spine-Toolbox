.. Spine Toolbox Dependencies
   Created 17.1.2019

************
Dependencies
************

Spine Toolbox requires Python 3.7 or Python 3.8. Python 3.9 is not supported yet.

The dependencies have been split to required packages and development packages. The required packages
must be installed for the application to start. The development packages contain tools that are
recommended for developers. If you want to deploy the application yourself by using the provided
*cx_Freeze_setup.py* file, you need to install the *cx_Freeze* package (v6.6 or newer recommended).

At the moment, Spine Toolbox depends on four main packages (*spinetoolbox*, *spine-engine*, *spine-items*,
and *spinedb-api*) developed in Spine project.
For version number limitations, please see `requirements.txt` and `setup.py` files in *spinetoolbox*,
*spine-engine*, *spine-items*, and *spinedb-api* packages

Dependencies by package
-----------------------

spinetoolbox
++++++++++++

+-------------------+---------------+
| Package name      |     License   |
+===================+===============+
| spinedb-api       |     LGPL      |
+-------------------+---------------+
| spine_engine      |     LGPL      |
+-------------------+---------------+
| spine_items*      |     LGPL      |
+-------------------+---------------+
| pyside2           |     LGPL      |
+-------------------+---------------+
| datapackage       |     MIT       |
+-------------------+---------------+
| jupyter-client    |     BSD       |
+-------------------+---------------+
| qtconsole         |     BSD       |
+-------------------+---------------+
| sqlalchemy        |     MIT       |
+-------------------+---------------+
| numpy             |     BSD       |
+-------------------+---------------+
| matplotlib        |     BSD       |
+-------------------+---------------+
| scipy             |     BSD       |
+-------------------+---------------+
| networkx          |     BSD       |
+-------------------+---------------+
| cx_Oracle         |     BSD       |
+-------------------+---------------+
| pandas            |     BSD       |
+-------------------+---------------+
| pymysql           |     MIT       |
+-------------------+---------------+
| pyodbc            |     MIT       |
+-------------------+---------------+
| psycopg2          |     LGPL      |
+-------------------+---------------+
| jill              |     MIT       |
+-------------------+---------------+

***** spine-items is not a 'hard' requirement of Spine Toolbox. The app does start without spine-items
but the features in that case are quite limited.

spinedb-api
+++++++++++

+-------------------+---------------+
| Package name      |     License   |
+===================+===============+
| sqlalchemy        |     MIT       |
+-------------------+---------------+
| alembic           |     MIT       |
+-------------------+---------------+
| faker             |     MIT       |
+-------------------+---------------+
| python-dateutil   |     PSF       |
+-------------------+---------------+
| numpy             |     BSD       |
+-------------------+---------------+
| openpyxl          |   MIT/Expat   |
+-------------------+---------------+
| gdx2py            |     MIT       |
+-------------------+---------------+
| ijson             |     BSD       |
+-------------------+---------------+

spine-engine
++++++++++++

+-------------------+---------------+
| Package name      |     License   |
+===================+===============+
| spinedb-api       |     LGPL      |
+-------------------+---------------+
| dagster           |  Apache-2.0   |
+-------------------+---------------+
| sqlalchemy        |     MIT       |
+-------------------+---------------+
| numpy             |     BSD       |
+-------------------+---------------+
| datapackage       |     MIT       |
+-------------------+---------------+

spine-items
+++++++++++

+-------------------+---------------+
| Package name      |     License   |
+===================+===============+
| spinetoolbox      |     LGPL      |
+-------------------+---------------+
| spinedb-api       |     LGPL      |
+-------------------+---------------+
| spine-engine      |     LGPL      |
+-------------------+---------------+

Development packages
--------------------

Below is a list of development packages in `dev-requirements.txt`. Sphinx and sphinx_rtd_theme
packages are needed for building the user guide. Black is used for code formatting while pylint
does linting. Pre-commit hook enables automatic code formatting at git commit.

+-------------------+---------------+
| Package name      |     License   |
+===================+===============+
| black             |     MIT       |
+-------------------+---------------+
| pre-commit        |     MIT       |
+-------------------+---------------+
| pyYAML            |     GPL       |
+-------------------+---------------+
| pylint            |     GPL       |
+-------------------+---------------+
| sphinx            |     BSD       |
+-------------------+---------------+
| sphinx_rtd_theme  |     MIT       |
+-------------------+---------------+
| recommonmark      |     MIT       |
+-------------------+---------------+
| sphinx-autoapi    |     MIT       |
+-------------------+---------------+
