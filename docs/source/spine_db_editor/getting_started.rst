***************
Getting started
***************

.. contents::
   :local:

Launching the editor
--------------------

From Spine Toolbox
==================

To open a single database in Spine database editor:

1. Create a *Data Store* project item.
2. Select the *Data Store*.
3. Enter the url of the database in *Data Store Properties*.
4. Press the **Open editor** button in *Data Store Properties*.

To open multiple databases in Spine database editor:

1. Repeat steps 1 to 3 above for each database.
2. Create a *View* project item.
3. Connect each *Data Store* item to the *View* item.
4. Select the *View* item.
5. Press **Open editor** in *View Properties*.

From the command line
=====================

To open a single SQLite database in Spine database editor, use the ``spine_db_editor.py`` script
in the ``bin`` folder::

    spine_db_editor.py "...path of the database file..."


Knowing the UI
--------------

The form has the following main UI components:

- *Entity trees* (*Object tree* and *Relationship tree*): 
  they present the structure of classes and entities in all databases in the shape of a tree.
- *Stacked tables* (*Object parameter value*, *Object parameter definition*, 
  *Relationship parameter value*, and *Relationship parameter definition*): 
  they present object and relationship parameter data in the form of stacked tables.
- *Pivot table* and *Frozen table*: they present data for a given class in the form of a pivot table,
  optionally with frozen dimensions.
- *Entity graph*: it presents the structure of classes and entities in the shape of a graph.
- *Tool/Feature tree*: it presents tools, features, and methods defined in the databases.
- *Parameter value list*: it presents parameter value lists available in the databases.
- *Alternative/Scenario tree*: it presents scenarios and alternatives defined in the databases.
- *Parameter tag*: it presents parameter tags defined in the databases.

.. tip:: You can customize the UI from the **View** and **Pivot** sections in the hamburger menu.

