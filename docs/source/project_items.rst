.. Project items documentation
   Created 19.8.2019

.. |data_connection| image:: ../../spinetoolbox/ui/resources/project_item_icons/file-alt.svg
   :width: 16
.. |importer| image:: ../../spinetoolbox/ui/resources/project_item_icons/database-import.svg
   :width: 16
.. |data_store| image:: ../../spinetoolbox/ui/resources/project_item_icons/database.svg
   :width: 16
.. |execute| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-solid.svg
   :width: 16
.. |execute-selected| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-regular.svg
   :width: 16
.. |exporter| image:: ../../spinetoolbox/ui/resources/project_item_icons/database-export.svg
   :width: 16
.. |tool| image:: ../../spinetoolbox/ui/resources/project_item_icons/hammer.svg
   :width: 16
.. |view| image:: ../../spinetoolbox/ui/resources/project_item_icons/binoculars.svg
   :width: 16
.. |folder-open| image:: ../../spinetoolbox/ui/resources/menu_icons/folder-open-solid.svg
   :width: 16

.. _Project Items:

*************
Project Items
*************

.. contents::
   :local:

Project items in the *Design view* and the connections between them make up the graph (Directed Acyclic
Graph, DAG) that is executed when the |execute| or |execute-selected| buttons are pressed.

See :ref:`Executing Projects` for more information on how a DAG is processed by Spine Toolbox. You can
also find information on how resources are passed between project items at execution time there.

Project Item Properties
-----------------------

Each project item has its own set of *Properties*. You can view and edit them by selecting a project
item on the *Design View*. The Properties are displayed in the *Properties* dock widget on the main
window. Project item properties are saved into the project save file (``project.json``), which can be
found in ``<proj_dir>/.spinetoolbox/`` directory, where ``<proj_dir>`` is your current project
directory.

In addition, each project item has it's own directory in the ``<proj_dir>/.spinetoolbox/items/``
directory. You can quickly open the project item directory in a file explorer by clicking on the
|folder-open| button located in the lower right corner of each *Properties* form.

Project Item Descriptions
-------------------------
The following items are currently available:

Data Store |data_store|
=======================

A Data store item represents a connection to a Spine model database.
Currently, the item supports sqlite and mysql dialects.
The database can be accessed and modified in :ref:`Data store view <Data store view>`
available from the item's properties or from a right-click context menu.

Data Connection |data_connection|
=================================

A Data connection item provides access to data files.
It also provides access to the :ref:`Datapackage editor <Spine datapackage editor>`.

Tool |tool|
===========

Tool is the heart of a DAG. It is usually the actual model to be executed in Spine Toolbox
but can be an arbitrary script or executable as well.
A tool is specified by its :ref:`specification <Tool specification editor>`.

View |view|
===========

A View item is meant for inspecting data from multiple sources using the
:ref:`Data store view <Data store view>`.
Note that the data is opened in read-only mode so modifications are not possible from the View item.

Importer |importer|
===================

This item provides the user a chance to define a mapping from tabulated data such as comma separated
values or Excel to the Spine data model.

Exporter |exporter|
===================

This item exports databases contained in a *Data Store* into :literal:`.gdx` format for GAMS Tools.
See :ref:`Importing and exporting data` for more information.
