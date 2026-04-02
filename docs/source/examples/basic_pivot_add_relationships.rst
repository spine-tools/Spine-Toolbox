.. |element| image:: ../../../spinetoolbox/ui/resources/menu_icons/element.svg
   :width: 16
   :alt:
.. |table| image:: ../../../spinetoolbox/ui/resources/menu_icons/table.svg
   :width: 16
   :alt:

.. _Adding Relationships in Pivot Table:

***********************************
Adding Relationships in Pivot Table
***********************************

In this tutorial, we will dive into the Pivot table
and learn how to add (and remove) multidimensional entities using the **Element** view.
You will need to have Database Editor open with the data from :ref:`First Relationship` loaded in it
before starting the tutorial.

Bonding Fish with Pivot Table
=============================

Let's add even more bonds to our dataset using the **Element** pivot view.
To access this view, click the |element| **Element** button on the toolbar at the top of Database Editor.
Changing the view will rearrange the docks on the window.
**Entity tree**, however, is still in its familiar position.

Select the Bond class in **Entity tree**,
so that the **Element** pivot knows what display.

The pivot table that occupies the center of the window now shows three columns:
The first two columns list the available entities
while the third column (with the checkboxes) tells whether the bond exists (checkbox is checked) or not (unchecked).
The table shows all possible combinations of Fish which means it shows all possible Bond entities.
Checking or unchecking the checkboxes will immediately either create or destroy bonds.
Play around with the checkboxes as much as you like,
perhaps noting how the **Entity tree** tries to desperately stay up-to-date with your changes.
You can use **Edit->Undo** (**Ctrl+Z**) or **Edit->Redo** (**Ctrl+Y**) to undo and redo changes,
if you want to spice things up a bit.

To add more fish in the soup,
select the empty cell at the lower left corner of the pivot table (Fish1 column).
Type :literal:`Otto` and press **Enter**.
This will add a new entity to the Fish class
and add all possible Bonds with :literal:`Otto` to the pivot table.
You can now create bonds between :literal:`Otto` and other fish.

Once you are happy with your bonds,
switch the layout back to the regular view by clicking the |table| **Table** button on the top toolbar.

Committing Changes
==================

Saving the changes we made in this tutorial is not absolutely necessary,
but if you want to, follow :ref:`Committing Changes`.
