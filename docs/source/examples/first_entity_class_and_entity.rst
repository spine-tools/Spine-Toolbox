.. |add_entities| image:: ../../../spinetoolbox/ui/resources/menu_icons/cube_plus.svg
   :width: 16
   :alt:
.. |commit| image:: ../../../spinetoolbox/ui/resources/menu_icons/check.svg
   :width: 16
   :alt:
.. |new_file| image:: ../../../spinetoolbox/ui/resources/menu_icons/file.svg
   :width: 16
   :alt:

.. _First Entity Class And Entity:

*****************************
First Entity Class And Entity
*****************************

This basic-level tutorial guides you through creating an entity class and an entity.

Adding Entity Classes
=====================

You need to have an empty Spine database to work through this short tutorial.
Open Spine Toolbox, select **File -> New DB Editor** to open the Database editor.
Then, click the |new_file| **New** button on the toolbar or select **File->New...** to create a fresh database.

First, we need some entity classes.
Entity classes are structural data that define the types of entities in the database.
Each type has a distinct set of parameters given by the parameter definitions of the class.

Let's add a class to called Fish to the database.
Right-click the *root* item on **Entity tree** to open the entity context menu and select **Add entity classes...**
This opens a dialog with a table.
The table can be filled with new classes by hand or by copy-pasting data from e.g. spreadsheet program.
Write :literal:`Fish` to the **entity class name** column.
You can also write a description and choose a suitable icon and color for the class.
The rest of the columns can be left as-is for now.
The classes defined in the table are added when you press **Ctrl+Enter** or click **Ok**.

Often, you do not need to create classes manually.
Instead, the classes may come from a tool provided by the model you are using.
For example, the SpineOpt plugin "Load template" populates the database with all classes
required by SpineOpt.

Adding Entities
===============

Entities are instances of the class with individual values for the parameters of the class.
With the Fish class in place, we can finally add some fish to our database!
Which famous fish come to your mind?

Next, we will add Nemo to the database.
Click the |add_entities| icon next to the Fish class in **Entity tree**
or right-click Fish and select **Add entities...**.
An **Add entities** dialog opens that works very similarly to the **Add Entity classes** dialog we used previously.
Here, write :literal:`nemo` to the *entity name* column and press **Ctrl+Enter** to accept the addition.
We have our first entity!

Committing Changes
==================

At this point it is a good idea to save our achievements.
This operation is called *committing* since Spine data is stored in an SQL database.
In case of file-backed databases like SQLite, the operation is pretty much like saving changes to a file.
Press **Ctrl+Enter** or click the |commit| **Commit** button on the toolbar at the top.
You are asked to provide a commit message before proceeding.
Write something like::

    Added Fish class and first fish, nemo.

and press **Ctrl+Enter** to accept, or click **Commit**.
This stores pending changes to the database.

Past commit messages can viewed from **Session->History...** which opens the **Commit viewer** dialog.
Selecting a commit from the dialog also displays affected items.
However, the dialog can only show the latest action (addition or update) for an item
due to limitations on how the commit data is stored.
Deleted items will not show in affected items at all.

Next Steps
==========

This tutorial continues on :ref:`First Parameter`
where we will expand the dataset by adding a parameter to the Fish class.
