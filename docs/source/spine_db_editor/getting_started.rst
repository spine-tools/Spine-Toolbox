***************
Getting started
***************

.. contents::
   :local:

Launching the editor
--------------------

From Spine Toolbox
==================

There are two different ways to open a single database in Spine database editor from Spine Toolbox:

Using a *Data Store* project item:

1. Create a *Data Store* project item.
2. Select the *Data Store*.
3. Enter the url of the database in *Data Store Properties*.
4. Press the **Open editor...** button in *Data Store Properties* or double-click the *Data Store* project item.

Without a *Data Store*:

1. From the main window select **File -> New DB Editor**.
2. Open the menu by clicking on the hamburger menu icon (☰) or by pressing **ALT+F** or **ALT+E**.
3. Select **Open...** to open an existing database, **New..** to create a new one or paste a database URL into
   the URL bar.

From the command line
=====================

To open a single database in Spine database editor, use the ``spine-db-editor`` 
application which comes with Spine Toolbox. After the virtual environment is activated
the editor can be opened with the following command::

    spine-db-editor "...url of the database..."

Note that for e.g. an SQLite database, the url should start with ``sqlite:///`` followed by the path.

Adding multiple databases to one editor
---------------------------------------

One editor window can have multiple tabs. New tabs can be added by pressing the plus-sign (**+**) in the tab bar.
In the newly created tab, databases can be opened once again with the instructions given above. Tabs can be deleted
from the editor by pressing the cross (**X**) inside a tab. The tabs can be dragged from the tab bar to create new
editor windows. Tabs from different windows can also be dragged into others, fusing them into the same editor window.
It is also possible to have multiple databases open in the same tab. This allows the simultaneous viewing and
modification of the databases data.

To open multiple SQLite databases in the same Spine database editor by file browser:

1. Open a database Database editor using any of the ways explained before.
2. Select **Add...** from the editor's hamburger menu (☰).
3. Browse to the directory of the SQLite file and open it.

By using the database URL:

1. Open a database Database editor using any of the ways explained before.
2. In the URL bar, after the already open database's URL add a semicolon ``;``
   and after that the URL of the other database to be opened in the same editor.

Knowing the UI
--------------

Spine Database Editor has the following main UI components:

- *Entity tree*:
  they present the structure of entities in all databases in the shape of a tree.
- *Stacked tables* (*Parameter value*, *Parameter definition*, *Entity alternative*):
  they present entity data in the form of stacked tables.
- *Pivot table* and *Frozen table*: they present data in the form of a pivot table,
  optionally with frozen dimensions.
- *Entity graph*: it presents the structure of classes and entities in the shape of a graph.
- *Parameter value list*: it presents parameter value lists available in the databases.
- *Alternative*: it presents alternatives defined in the databases.
- *Scenario tree*: it presents scenarios defined in the databases.
- *Metadata*: presents metadata defined in the databases.
- *Item metadata*: shows metadata associated with the currently selected entities or parameter values.

.. tip:: You can customize the UI from the **View** section in the hamburger ☰ menu. There the **Docks...**
         menu can be used to enable and disable the different UI components listed above.

In the next section you will learn more about the different UI components and views available in the editor
