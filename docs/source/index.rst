.. Spine Toolbox documentation master file, created by
   sphinx-quickstart on Mon Jun 18 12:58:32 2018.
   Author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>

Welcome to Spine Toolbox's documentation!
=========================================

Spine Toolbox is an application, which provides means to define, manage, and execute complex data processing and
computation tasks, such as energy system models.

..  toctree::
    :maxdepth: 1
    :caption: Contents:

    tutorial
    contribution_guide
    code_ref

Terminology
===========
The following is a list of definitions that are used throughout the documentation and in the application itself.

Spine project Terminology
_________________________

- **Case study** Spine project has 13 case studies that help to improve, validate and deploy
  different aspects of the Spine Model and Spine Toolbox.
- **Data Interface** is a component in Spine Toolbox, which handles connecting to and importing
  from external data sources.
- **Data Package** is a data container format consisting of a metadata descriptor file
  (‘datapackage.json’) and resources such as data files.
- **Data sources** are all the original, unaltered, sources of data that are used to generate
  necessary input data for Spine Toolbox tools.
- **Scenario** A scenario combines data connections to form a meaningful data set for the target tool.
- **Spine data structure** Spine data structure defines the format for storing and moving data within
  Spine Toolbox. A generic data structure allows representation of many
  different modelling entities. Data structures have a class defining the type of
  entity they represent, can have properties and can be related to other data
  structures. Spine data structures can be manipulated and visualized within
  Spine Toolbox while Spine Model will be able to directly utilize as well as
  output them.
- **Spine Model** An interpreter, which formulates a solver-ready mixed-integer optimization
  problem based on the input data and the equations defined in the Spine
  Model. Outputs the solver results.
- **Use case** Potential way to use Spine Toolbox. Use cases together are used to test the
  functionality and stability of Spine Toolbox and Spine Model under different
  potential circumstances.

Spine Toolbox Terminology
_________________________

- **Spine Toolbox Project** is a Toolbox concept and consists of a data processing chain that
  is built by the user for solving a particular problem. Current items that constitute a project are;
  Data Connection, Data Store, Tool, and View. There can be any number of these items in a project, and
  they can be connected by drawing links between them.
- **Data Connection** is a project item, which facilitates data transfer from original data sources,
  e.g. spreadsheet files or databases, to Spine Toolbox. The original data source file does not need to
  conform to the format that Spine Toolbox is capable of reading, since there is an interpreting layer
  between them (Data Interface).
- **Data Store** is a Spine Toolbox internal data container which follows the Spine data
  model. A data store is implemented using a database, it may be, for example, an SQL database.
- **Tool** can be a computation process or a simulation model, or it can also be a script to
  convert data or calculate a new variable. Tool takes some data as input and produces an output.
  Tool contains a reference to the model code, external program that executes the code, and input
  data that the model code requires. Spine Model is a Tool from Spine Toolbox's point-of-view.
- **View** A project item that can be used for visualizing project data.

Dependencies
============
Spine Toolbox uses code from the following packages and/or projects. You need the optional packages for
building the user guide and for deploying the application.

+------------------+--------------+--------------+
| Package name     |    Version   |    License   |
+==================+==============+==============+
| **Required packages**                          |
+------------------+--------------+--------------+
| pyside2          | 5.6          |    LGPL      |
+------------------+--------------+--------------+
| datapackage      | 1.2.3        |    MIT       |
+------------------+--------------+--------------+
| pyodbc           | 4.0.23       |    MIT       |
+------------------+--------------+--------------+
| pymysql          | 0.9.2        |    MIT       |
+------------------+--------------+--------------+
| qtconsole        | 4.3.1        |    BSD       |
+------------------+--------------+--------------+
| sqlalchemy       | 1.2.6        |    MIT       |
+------------------+--------------+--------------+
| openpyxl         | 2.4.0        |  MIT/Expat   |
+------------------+--------------+--------------+
| spinedatabase_api| 0.0.1        |    LGPL      |
+------------------+--------------+--------------+
| **Optional packages**                          |
+------------------+--------------+--------------+
| sphinx           | 1.7.5        |    BSD       |
+------------------+--------------+--------------+
| sphinx_rtd_theme | 0.4.0        |    MIT       |
+------------------+--------------+--------------+
| recommonmark     | 0.4.0        |    MIT       |
+------------------+--------------+--------------+
| cx_Freeze        | 6.0b1        | PSFL (deriv.)|
+------------------+--------------+--------------+

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
