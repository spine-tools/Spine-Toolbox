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

.. _Project Items:

*************
Project Items
*************

Project items in the *Design view* and the connections between them make up the graph (Directed Acyclic Graph, DAG)
that is executed when the |execute| or |execute-selected| buttons are pressed.

See :ref:`Executing Tools` for more information on how the DAG is processed by Spine Toolbox.

The following items are currently available:

Data Store |data_store|
-----------------------

A Data store item represents a connection to a Spine model database.
Currently, the item supports sqlite and mysql dialects.
The database can be accessed and modified using :ref:`data store views <Data store views>`
available from the item's properties or from a right-click context menu.

Data Connection |data_connection|
---------------------------------

A Data connection item provides access to data files.
It also provides access to the :ref:`Datapackage editor <Spine datapackage editor>`.

Tool |tool|
-----------

Tool is the heart of a DAG. It is usually the actual model to be executed in Spine Toolbox
but can be an arbitrary script or executable as well.
A tool is specified by its :ref:`specification <Tool specification editor>`.

View |view|
-----------

A View item is meant for inspecting data from multiple sources using the
:ref:`data store views <Data store views>`.
Note that the data is opened in read-only mode so modifications are not possible from the View item.

.. note::

   Currently, only *Tree view* supports multiple databases.

Importer |importer|
-------------------

This item provides mapping from tabulated data such as comma separated values or Excel to the Spine data model.

Exporter |exporter|
-------------------

This item exports databases contained in a *Data Store* into :literal:`.gdx` format for GAMS Tools.
See :ref:`Importing and exporting data` for more information.