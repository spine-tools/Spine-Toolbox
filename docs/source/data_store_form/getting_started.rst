***************
Getting started
***************

.. contents::
   :local:

Launching the form
------------------

From Spine Toolbox
==================

To open a single database in Data store form:

1. Create a *Data Store* project item.
2. Select the *Data Store*.
3. Enter the url of the database in *Data Store Properties*.
4. Press the **Open form** button in *Data Store Properties*.

To open multiple databases in Data store form:

1. Repeat steps 1 to 3 above for each database.
2. Create a *View* project item.
3. Connect each *Data Store* item to the *View* item.
4. Select the *View* item.
5. Press **Open DS form** in *View Properties*.

From the command line
=====================

To open a single SQLite database in Data store form, use the ``open_ds_form.py`` script in the ``bin`` folder::

    open_ds_form.py "...path of the database file..."


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
- *Parameter value list*: it presents parameter value lists available in the database.
- *Parameter tag toolbar*: it presents parameter tags defined in the database.

.. tip:: You can show or hide form components using the **View** menu,
   or select among three predefined layout styles: **Stacked style**, **Pivot style**, and **Graph style**.

