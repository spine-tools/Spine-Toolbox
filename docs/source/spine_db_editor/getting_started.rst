.. |reload| image:: ../../../spinetoolbox/ui/resources/menu_icons/sync.svg
   :width: 16
.. |database| image:: ../../../spinetoolbox/ui/resources/database.svg
   :width: 16

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

It is possible to open multiple databases in the same editor. This allows one to view and modify
the data of the open databases in one editor.

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

When you open an empty database for the first time in a Spine Database Editor, it should look something
like this:

.. image:: img/plain_db_editor.png
   :align: center

The dock widgets can be scaled by dragging them from the sides and moved around by dragging them from their
darker colored headers. Like with other widgets, Toolbox remembers the customizations and the editor will
open in the same configuration when it is opened the next time. If the view is changed from the hamburger
menu the modifications will be lost and the UI will be reverted back to default.

Tab bar
=======

The uppermost UI element is the tab bar. One editor window can have multiple tabs. New tabs can be added by
pressing the plus-sign (**+**) in the tab bar. In the newly created tab, databases can be opened once again
with the instructions given above. Tabs can be deleted from the editor by pressing the cross (**X**) inside
a tab. The tabs can be dragged from the tab bar to create new editor windows. Tabs from different windows
can also be dragged into others, fusing them into the same editor window.

Navigation bar
==============

Right below the tab bar there is the navigation bar. With the backwards and forwards arrows it is possible
to go back to the database that was previously loaded in the specific tab. This is kind of analogous of web
browsers and going back to the previous page. Next to the arrows there is the **reload** (|reload|) button.
It can be used to reload the data of the database. Next up is the Data Store icon (|database|) which lists
the Data Store items in the project and can be used to open any of them in the current tab. The URL bar
contains the URL of the databases tha are currently open in the tab. As mentioned before, databases can
be opened by inserting valid database URLs into this field and pressing enter. The URL bar also contains
the filter (more about this later). After the URL bar there is the Spine-Toolbox logo which when clicked
brings up the Spine-Toolbox main window. Finally there is the hamburger menu (☰) which holds much of the
power of the Spine Database Editor (more on this also later).

Hamburger menu
==============

WIP

Filter
======

WIP

Views and trees
===============

WIP

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
