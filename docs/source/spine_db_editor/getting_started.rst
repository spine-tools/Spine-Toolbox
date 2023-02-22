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
4. Press the **Open editor...** button in *Data Store Properties* or double-click the *Data Store* project item.

To open multiple SQLite databases in Spine database editor:

1. Open a database in Database editor as explained above.
2. Select **Add...** from the ☰ menu.
3. Open the SQLite file.

From the command line
=====================

To open a single database in Spine database editor, use the ``spine-db-editor`` 
application which comes with Spine Toolbox::

    spine-db-editor "...url of the database..." 

Note that for e.g. an SQLite database, the url should start with ‘sqlite:’.


Knowing the UI
--------------

The form has the following main UI components:

- *Entity trees* (*Object tree* and *Relationship tree*): 
  they present the structure of classes and entities in all databases in the shape of a tree.
- *Stacked tables* (*Object parameter value*, *Object parameter definition*, 
  *Relationship parameter value*, and *Relationship parameter definition*): 
  they present object and relationship parameter data in the form of stacked tables.
- *Pivot table* and *Frozen table*: they present data in the form of a pivot table,
  optionally with frozen dimensions.
- *Entity graph*: it presents the structure of classes and entities in the shape of a graph.
- *Tool/Feature tree*: it presents tools, features, and methods defined in the databases.
- *Parameter value list*: it presents parameter value lists available in the databases.
- *Alternative tree*: it presents alternatives defined in the databases.
- *Scenario tree*: it presents scenarios defined in the databases.
- *Metadata*: presents metadata defined in the databases.
- *Item metadata*: shows metadata associated with the currently selected entities or parameter values.

.. tip:: You can customize the UI from the **View** and **Pivot** sections in the hamburger ☰ menu.

