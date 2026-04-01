.. |add_entities| image:: ../../../spinetoolbox/ui/resources/menu_icons/cube_plus.svg
   :width: 16
   :alt:
.. |remove_rows| image:: ../../../spinetoolbox/ui/resources/menu_icons/cube_minus.svg
   :width: 16
   :alt:

.. _First Relationship:

******************
First Relationship
******************

This is a basic level tutorial where we will build multidimensional entities, also known as relationships.
You are expected to have completed :ref:`First Entity Class And Entity` before starting this tutorial.
If not already open, launch Spine Database Editor and open the database
that contains the Fish class and an entity only known as :literal:`nemo` to humankind.

Adding Multidimensional Entity Classes
======================================

Multidimensional entity classes are used to connect two or more classes with each other.
The connections represent relations, links, groupings or similar concepts in the data structure.
One dimensional entity classes connecting a single class to nothing are possible, too, but uncommon.
While the dimensions are usually zero dimensional classes,
they can also be other multidimensional classes.

For the sake of simplicity, we will create a two dimensional entity class called Bond
that connects the Fish class back to Fish class.
Since we will use Fish as the first dimension,
**right-click** on Fish in **Entity tree** and select **Add entity classes...** from the popup menu.
The **Add entity classes** dialog appears.

Note, that at the top of the dialog, the **Number of dimensions** spin box is readily set to one,
and :literal:`Fish` is written to the first cell of the table below.
Now, increase the number of dimensions to two which adds a *dimension name (2)* column to the table.
**Double-clicking** the cell in *dimension name (2)* or selecting the cell and pressing **F2** (shortcut for edit)
opens a list of available entity classes.
Select :literal:`Fish` from the list with arrow keys and **Tab** or by mouse.

Once you have selected the second dimension,
the new class gets assigned a name, :literal:`Fish__Fish`, automatically.
Sometimes the generated name is OK.
However, we want a more descriptive one, so type :literal:`Bond` into the cell.
Pressing **Tab** will accept the edit and move on to the next column, *description*.
Write :literal:`A bond between two fish.` or whatever you fancy into the cell,
then press **Tab** again which starts editing the cell under *display icon*
which in turn shows the **Select icon and color** dialog.

Select some nice icon and equally nice color for Bond.
You can use the search bar below the **Font Awesome icons** label to narrow down the icon selection.
Some slots in the selection show just a blank space.
It is unclear whether this is a bug or a feature.
Unlike most other dialogs in Database Editor, this one cannot be accepted by **Ctrl+Enter**.
However, **Enter** works, or you can click the **OK** button.

Back in the **Add entity classes** dialog, press **Ctrl+Enter** to add the class, or click **OK**.
The new class should appear in **Entity tree**.

Why did Bond appear below Fish? How is **Entity tree** sorted?
The answer is that classes are primarily sorted by the number of dimensions
with zero dimensional classes at the top.
Alphabetic sorting is just secondary.

Lastly, the description we added to Bond can be viewed as a tooltip.
Point your mouse to the Bond item in **Entity tree**.
After a second or two a tooltip should appear showing the text you entered in the *description* column.

Adding More Fish
================

We need more fish to bond.
Add the following entities to the Fish class: :literal:`marlin`, :literal:`bruce` and :literal:`cheep cheep`.
In the **Add entities** dialog you can enter the name of the first Fish to the table,
then press **Down arrow** to create a new empty row and move down to the new empty cell.
This is a convenient way to add multiple entities at the same time.

Bonding Fish with Add Entities Dialog
=====================================

There are multiple ways to bond fish, that is, to add new entities to the Bond class.
Here we will use the familiar **Add entities** dialog.
Other tutorials will guide you through the other methods.
Once you are more experienced with the tools at your disposal,
you will be able to choose the best suited method for your needs, use case and mojo.

**Right-click** Bond in the tree and select **Add entities...** from the popup menu
or click the |add_entities| icon next to Bond.
Note, that on the left of the *entity name* column,
the **Add entities** dialog now has two additional columns, both named *Fish*.
They represent the two dimensions of the entity class.
The entities that make up a Bond entity are called *elements*.

Select the cell below the first *Fish* column and start typing :literal:`nemo` into it.
Notice, that a list of Fish entities appears below, filtered by what you have typed.
Once only :literal:`nemo` is shown on the list, press **Tab** to accept
which also moves the selection to the next *Fish* column.
Add :literal:`marlin` to that cell either by typing or selecting from the list.

Now that the elements of the first Bond entity are in place,
the *entity name* column readily contains an automatically generated name, :literal:`nemo__marlin`.
We will leave the name as-is.
It is rather uncommon to rename the multidimensional entities
as they are usually referenced by their bynames, in this case :literal:`nemo | marlin`.

Now add :literal:`nemo | bruce`, :literal:`nemo | cheep cheep` and :literal:`bruce | marlin` entities.
Try to use both mouse and keyboard (arrow keys, **F2**, **Tab**, **Enter**) to fill in the table!
You can even copy some Fish names from this tutorial and paste them on the table.

If you make mistakes, you can remove erroneous rows with the |remove_rows| **Remove selected rows** button,
or clear cells with the **Delete** or **Del** keys.
Try them out even if you do not make mistakes!

After having some fun with the dialog, press **Ctrl+Enter** or click **OK** to accept.
Expand the Bond class in **Entity tree** to check that all bonds are there.
Note that the list shows the bynames, not the actual names of the entities.

Committing Changes
==================

We have added quite a bit of new items to the data.
Now is as good time as any to commit the changes.

Next Steps
==========

To learn about other tools in Database Editor that can be used to add multidimensional entities,
head on to :ref:`Adding Relationships in the Manage Elements Dialog`
or :ref:`Adding Relationships in Pivot Table`.
