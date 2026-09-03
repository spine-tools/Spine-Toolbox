.. |open_file| image:: ../../../spinetoolbox/ui/resources/menu_icons/folder-open-solid.svg
   :width: 16
   :alt:

.. _First Parameter:

***************
First Parameter
***************

In this basic-level tutorial, we will create a parameter definition,
and add a parameter value to an entity.
This tutorial is based on :ref:`First Entity Class And Entity`.
If you have completed the tutorial previously,
start Spine Toolbox, select **File -> New DB Editor** to open the Database editor.
Then, click the |open_file| **Open** icon on the toolbar or select **File->Open...** to open the database
you used for the tutorial.

Adding Parameter Definitions
============================

Let's define a parameter for Fish.
Press **Alt+Shift+3** or click the **Parameter definition** tab to bring the **Parameter definition** dock into focus.
The dock contains two tables:
The top one is currently empty, but usually it shows existing parameters.
You can view current parameters as well as modify them here.
The bottom one is called *empty table* and it is used to add new parameters.

Select Fish from the Entity tree.
This will fill the *class* column in **Parameter definition** dock with the correct data.
Write :literal:`speed` into the *parameter name* column.
Upon pressing **Enter**, the empty row gets accepted as a proper parameter definition
and the row from the empty table is moved to the top table.

In addition to filling the empty rows by hand, it is possible to copy-paste data from a spreadsheet to the empty table.

Adding Parameter Values
=======================

Above, we defined a :literal:`speed` parameter for Fish, and now we will set it for :literal:`Nemo`.
Press **Alt+3** to focus on the **Parameter value** dock
or click the name of its tab.
The dock should feel familiar.
Indeed, it works much like the **Parameter definition** dock.
Select Nemo from the **Entity tree**.
You may need to expand the fish class with the small arrow on the left first.
This will fill the *class* and *entity byname* columns of the parameter value table with correct values.

:emphasis:`What is a byname, anyway?
In case of zero-dimensional entities, like Nemo, it is just the name of the entity.
In other tutorials, we will create multidimensional entities, i.e. relationships.
In that case, entity byname is a list of the names of the zero-dimensional parts of the relationship.`

:emphasis:`Let's get back to parameter values.`

Double-click the cell under the *parameter name* column on the empty row in **Parameter value** dock.
This opens a list of available parameters in the Fish class.
Select :literal:`speed` from the list by pressing the **Down arrow**
and hit **Tab** to move to the next column.
You can also select :literal:`speed` by mouse.

The *alternative* column works the same way as *parameter name*:
editing a cell opens a list of available alternatives.
Currently, the only option is :literal:`Base`
which readily exists in every freshly created Spine database.

:emphasis:`We will discuss alternatives in more depth in other tutorials.
For now, it is enough to say that alternatives allow different values for the same parameter,
creating a basis for scenarios.`

Select :literal:`Base` with the arrow keys and move on to the next column using **Tab**.

The last column, *value*, contains the actual speed of :literal:`Nemo` (in the :literal:`Base` alternative).
Enter **5** and press **Enter** to accept the row.
A new row containing the added value should now appear on the table above the empty row
while the empty row gets cleared.
Congratulations, you have just created a parameter value!

Committing Changes
==================

This is a good point to save the changes by committing them.
If you are not sure how to do that, visit :ref:`Committing Changes`.

Next Steps
==========

The tutorial continues on :ref:`First Relationship`
where we will expand the set of entity classes and entities
into multiple dimensions. See you there!
