..  Tutorial for Spine Toolbox
    Author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>, Manuel Marin <manuelma@kth.se>
    Date created: 18.6.2018

.. |ds_icon| image:: ../../spinetoolbox/ui/resources/ds_icon.png
             :width: 24
.. |plus| image:: ../../spinetoolbox/ui/resources/plus.png
          :width: 16
.. |minus| image:: ../../spinetoolbox/ui/resources/minus.png
           :width: 16
.. |import| image:: ../../spinetoolbox/ui/resources/import.png
            :width: 16
.. |Spine| image:: ../../spinetoolbox/ui/resources/Spine_symbol.png
          :width: 16

Tutorial
========

Welcome to the tutorial for Spine Toolbox. This tutorial covers the following topics:

.. contents::
   :local:


Knowing the Interface
---------------------

The Spine Toolbox interface revolves around the **Main View**,
where you can visualize and manipulate your project in a pictorial way.
Alongside **Main view** there are a few *docked widgets*:

- **Project** provides more concise views of your project into three tabs:

   - *Items* lists project items grouped by category:
     Data Stores, Data Connections, Tools and Views.
   - *Connections* shows connections between items.
   - *Templates* lists Tool templates that Tool items can run.

- **Item Controls** shows controls for the currently selected item.
- **Event Log** outputs informative messages, and also errors and warnings.
- **Subprocess Output** shows the output of command line tools.
- **Julia REPL** is the console where Julia tools are executed.

.. tip:: You can drag-and-drop the docked widgets around the screen,
   customizing the interface at your will.
   Also, you can select which ones are shown/hidden using either the **View** menu,
   or the *Add Item* toolbar's context menu.
   Spine Toolbox will remember your configuration between sessions.

.. tip:: Most elements in the Spine Toolbox's interface are equipped with *tool tips*. Leave your mouse
   cursor over an element (button, view, etc.) for a moment to make the tool tip appear.

Creating a Project
------------------

In the main menu bar, click **File**, **New...** to open the *New Project* form.
Type 'tutorial' in the name field ---we will leave the description empty this time--- and click **Ok**.

Congratulations, you have created a new project.

.. tip:: You can also create a new project with the keyboard combination *Ctrl+N*.

Working with Data Stores
------------------------

Let's add a Data Store to the project. You can do this in two different ways:

A) In the main menu bar, click **Edit**, **Add Data Store**.
B) Drag-and-drop the *Data Store* icon (|ds_icon|) from the *Add Item* toolbar onto the *Main View*.

The *Add Data Store* form will appear.
Type 'simple test system' in the name field and click **Ok**.
Now you should see the newly added item in the *Main View*, and also in the *Project* widget, *Items* tab. It should
look similar to this:

.. image:: img/simple_test_system.png
   :align: center

.. note:: The dotted square in the center of the item's figure is the *connector* button,
   and serves to make connections
   between this and other items in your project. You don't have other items yet so we'll leave
   this button alone for now.

Click anywhere in the Data Store item (outside of the connector button) to select it.

.. tip:: You can also select a project item
   by clicking on its name in the *Project* widget, *Items* tab.

With the Data Store item selected,
the *Item Controls* area should show two lists ---both empty for now---, *References* and *Data*:

- **References** lists sources where this Data Store can import data from. (These typically live *outside*
  the current Spine Toolbox project.)
- **Data** lists the contents of this Data Store's folder, where imported data is saved.
  You can open this folder in your file explorer by clicking **Open directory**.


Creating a new Spine database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's add data to this Data Store.
Click on the *Spine* button (|Spine|) under *Item controls*.
In the popup dialog, type 'simple' as the database name and click **Ok**.

Now you should see a new item in the *Data* list:

.. image:: img/data_store_simple_sqlite.png
   :align: center


Using the Spine Data Store form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Double click on the 'simple.sqlite' file we've just created to open the **Spine Data Store** form. This is
a dedicated interface that you can use to manipulate databases in the Spine format. The interface is
divided in three main areas:

- **Object tree** displays the database contents into a tree,
  with object classes at the top level.
- **Object parameter** displays parameters associated with the object that is
  currently selected in the *Object tree*.
- **Relationship parameter** displays parameters associated with
  any relationships involving the currently selected object.

Right now you should see a list of pre-defined object classes in the *Object tree*.

.. note:: These pre-defined classes
   correspond to the *generic data structure* that Spine uses to define energy models.

Let's add a new object to the 'unit' object class. Right-click over the item tagged 'unit' in the *Object tree*
and select **Add object** from the context menu. In the popup dialog,
enter 'coal_import' in the name field and click **Ok**. Now you
should see the newly added object in the *Object tree*, under the 'unit' class.

Repeat the operation to add an object called 'Leuven' to the 'node' class.

Now let's add a relationship class between the 'node' and 'unit' object classes.
Right-clik on 'node' to display
the context menu, and this time select **Add relationship class**.
Enter 'node_unit' in the name field,
and select 'unit' from the drop-down list. Click **Ok** when you are done.
An item named 'node_unit' should appear now *both* under the 'coal_import' and 'Leuven' objects,
as below:

.. image:: img/object_tree_node_unit.png
  :align: center

Let's add a relationship of class 'node_unit' between the two objects we've created.
Right-click on the 'node_unit' relationship class
below the 'coal_import' object and select **Add relationship** in the context menu.
Enter 'Leuven_coal_unit' in the name field and select 'Leuven' from the drop-down list (it should be
the only option available). Click **Ok**.

After this you should see an item called 'Leuven' under the 'node_unit' relationship class
(under the 'coal_import' object),
representing the newly added relationship.

Now expand the 'node_unit' relationship class under the 'Leuven' object. Here you will find an item named 'coal_import',
representing the same relationship but in the opposite sense:

.. image:: img/Leuven_coal_import.png
  :align: center

.. important:: Relationships in Spine are *omni-directional* (in simple terms, they work both ways).
   Therefore, for every relationship  you create, Spine Toolbox creates the symmetric relationship
   for you.

Let's go one step ahead and add a couple of parameters to the 'unit' class. Right click on 'unit'
and select **Add parameter** in the context menu.
Type 'conversion_cost' in the name field and press *Enter*.
This will automatically activate
the *Definition* tab in the *Object parameter* pane and highlight the newly inserted
parameter.

.. note:: Don't worry about the other fields in the *parameter* table for now. They are
   only there to support more sophisticated parameter definitions to be used, for instance,
   in time-varying energy models.

Repeat the operation to add a parameter named 'capacity_to_flow' to the 'unit' class. After this, you
should see something like this in the *Object parameter* pane, *Definition* tab:

.. image:: img/parameter_definition.png
  :align: center

To finish our session with the *Spine Data Store* form, we will add a new parameter value. Right-click
on the 'coal_import' object under the 'unit' class, and select **Add parameter value** in the
context menu. In the drop-down list you should see the two parameters we have just
created. Select 'conversion_cost', type '12' in the value field and click **Ok** (don't worry
about the json field just yet).
This will automatically activate the *Value* tab in the *Object parameter* pane,
and highlight the newly inserted parameter value:

.. image:: img/parameter_value.png
  :align: center

It's time to save our work. In the menu bar, click **Session**, **Commit**,
type 'Add coal_import, Leuven, and conversion_cost.' (or any other meaningful message)
and click **Ok**. All changes have now been committed to the 'simple.sqlite' database.

Select **Session**, **Close**, to close your session and go back to the main interface.

Now click on **Open directory** under
*Item Controls*. This will open your file explorer in the folder associated with
this Data Store.
You should see the 'simple.sqlite' file sitting there.
Take note of the file's path for the next step.
If you are running Spine Toolbox on Windows installed in the default location, the path should
be something like this:
``C:\\SpineToolbox-0.0.13\projects\tutorial\simple_test_system\simple.sqlite``.


Adding an SQLite reference
~~~~~~~~~~~~~~~~~~~~~~~~~~

Just for illustration purposes, we will add a reference to the recently created 'simple.sqlite'
file. Please note that this is not something you would typically do in a real project.

Add a new *Data Store* item to the project and call it 'simple_reference'. Select this new item
to show its *Item Controls*, and
click on the plus button (|plus|) to open the *Add Database Reference* form.

.. note:: The *Add Database Reference* form allows you to access Spine databases in a number of
   SQL dialects. If you try to use a dialect that's currently not supported by your system,
   Spine Toolbox will offer to install the necessary packages for you. Just choose the
   appropriate package manager (*conda* or *pip*) when prompted. If you're unsure
   about which package manager to choose, it's usually safe to try one and then the other and see
   what works.


Select the 'sqlite' dialect in the drop-down list at the top,
and click on the **Browse...** button. This will
open a system dialog to let you
select an SQLite file from your computer. Find the 'simple.sqlite' file (recall the path
from the previous step) and click **Open**. Back in the *Add Database Reference* form, click
**Ok**. Now you should see an item called 'simple.sqlite' in the *References*
list.

You can open the 'simple.sqlite' reference using the *Spine Data Store* form by double-clicking on it (much in
the same way as you did with the 'simple.sqlite' file in the other Data Store).
Go ahead and do it. You will find the exact same
content that you just inserted in the 'simple.sqlite' database before.
Close the *Spine Data Store* form to go back to the main interface.

.. tip:: To remove a reference, select it by clicking on its name
   and then press the *minus* button (|minus|).
   You can also remove all references at once by pressing this button while nothing is selected.

.. tip:: You can share the 'simple.sqlite' file with other Spine Toolbox users so they can see
   (and possible continue) your work. All they need to do is add a reference to the 'simple.sqlite'
   file in their project, using the procedure we have just described.


Importing references
~~~~~~~~~~~~~~~~~~~~

Select the 'simple.sqlite' reference in the *References* list and then click on the *import* button (|import|).
This will copy the 'simple.sqlite' database into a file called 'simple.sqlite' in the Data Store folder.
After this, the *Item Controls* should look similar to this:

.. image:: img/item_controls_data_store_import.png
  :align: center


.. TODO
.. Working with Data Connections
.. -----------------------------
..
..
.. Working with Tools
.. ------------------
..
..
.. Using the Julia REPL
.. --------------------
..
..
.. Miscellaneous
.. -------------
