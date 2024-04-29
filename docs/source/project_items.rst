.. Project items documentation
   Created 19.8.2019

.. |data_connection| image:: ../../spinetoolbox/ui/resources/project_item_icons/data_connection.svg
   :width: 16
   :alt:
.. |data_store| image:: ../../spinetoolbox/ui/resources/project_item_icons/database.svg
   :width: 16
   :alt:
.. |data_transformer| image:: ../../spinetoolbox/ui/resources/project_item_icons/paint-brush-solid.svg
   :width: 16
   :alt:
.. |execute| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
   :width: 16
.. |execute-selected| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-regular.svg
   :width: 16
.. |exporter| image:: ../../spinetoolbox/ui/resources/project_item_icons/database-export.svg
   :width: 16
   :alt:
.. |folder-open| image:: ../../spinetoolbox/ui/resources/menu_icons/folder-open-regular.svg
   :width: 16
.. |importer| image:: ../../spinetoolbox/ui/resources/project_item_icons/database-import.svg
   :width: 16
   :alt:
.. |merger| image:: ../../spinetoolbox/ui/resources/project_item_icons/blender.svg
   :width: 16
   :alt:
.. |tool| image:: ../../spinetoolbox/ui/resources/project_item_icons/hammer.svg
   :width: 16
   :alt:
.. |view| image:: ../../spinetoolbox/ui/resources/project_item_icons/binoculars.svg
   :width: 16
   :alt:

.. _Project Items:

*************
Project Items
*************

.. contents::
   :local:

Project items in the *Design view* and the connections between them make up the graph (Directed Acyclic
Graph, DAG) that is executed when the |execute| or |execute-selected| buttons are pressed.

See :ref:`Executing Projects` for more information on how a DAG is processed by Spine Toolbox.
Those interested in looking under the hood can check the :ref:`Project item development` section.

Project Item Properties
-----------------------
Each project item has its own set of `properties`. You can view and edit them by selecting a project
item in the **Design View**. The properties are displayed in the **Properties** dock widget on the main
window. Project item properties are saved into the project save file (``project.json``), which can be
found in ``<proj_dir>/.spinetoolbox/`` directory, where ``<proj_dir>`` is your current project
directory.

In addition, each project item has its own directory in the ``<proj_dir>/.spinetoolbox/items/``
directory. You can quickly open the project item directory in a file explorer by clicking the
|folder-open| button located in the upper right corner of each **Properties** form.

Project Item Descriptions
-------------------------
The following items are currently available:

Data Connection |data_connection|
=================================

A Data connection item provides access to data files.
The item has two categories of files: **references** connect to
files anywhere on the file system or on remote (non-Spine) databases while
**data** files reside in the item's own data directory.

Data Store |data_store|
=======================

A Data store item represents a connection to a (Spine) database.
Currently, the item supports sqlite and mysql dialects.
The database can be accessed and modified in :ref:`Spine db editor <Spine db editor>`
available by double-clicking a Data store on the Design view,
from the item's properties,
or from a right-click context menu.

Data Transformer |data_transformer|
===================================

Data transformers set up database manipulators for successor
items in a DAG. They do not transform data themselves;
rather, Spine Database API does the transformations configured
by Data transformers when the database is accessed.
Currently supported transformations include entity class and
parameter renaming as well as value transformations.

Exporter |exporter|
===================

Exporter outputs database data into tabulated file formats
that can be consumed by Tool or be used by external software
for analysis. See :ref:`Importing and exporting data` for more information.

Importer |importer|
===================

This item provides the user a chance to define a mapping from
tabulated data such as comma separated values or Excel to the Spine
data model. See :ref:`Importing and exporting data` for more information.

Merger |merger|
===============

A Merger item transfers data between Data Stores.
When connected to a single source database,
it simply copies data from the source to all output Data Stores.
Data from more than one source gets merged to outputs.

Tool |tool|
===========

Tool is the heart of a DAG. It is usually the actual model to be executed in Spine Toolbox
but can be an arbitrary script, executable or system command as well.
A Tool is specified by its :ref:`specification <Tool specification editor>`.

View |view|
===========

A View item is meant for plotting preselected parameter values from multiple sources.
