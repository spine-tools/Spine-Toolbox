
Removing data
-------------

This section describes the available tools to remove data.

.. contents::
   :local:

Removing entities and classes
=============================

Using *Remove items* dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Select the items in *Object tree* or *Relationship tree* corresponding to the entities and classes
you want to remove. Then, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection and choose **Remove selected items** from the context menu.

The *Remove items* dialog will popup:

.. image:: img/remove_entities_dialog.png
   :align: center

Specify the databases from where you want to remove each item under the *databases* column,
and press **Ok**.

Using *Entity graph*
~~~~~~~~~~~~~~~~~~~~

Select the items in *Entity graph* corresponding to the objects and/or relationships you want to remove.
Then, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection and choose **Remove selected items** from the context menu.


Using *Pivot table*
~~~~~~~~~~~~~~~~~~~
To remove objects or relationships from a specific class, bring the class to *Pivot table*
using the **Parameter value** input type
(see :ref:`using_pivot_table_and_frozen_table`),
and select the cells in the table headers corresponding to the objects and/or relationships you want to remove.
Then, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection and choose **Remove selected items** from the context menu.

Alternatively, to remove relationships for a specific class, 
bring the class to *Pivot table* using the **Relationship** input type
(see :ref:`using_pivot_table_and_frozen_table`).
The *Pivot table* headers will be populated
with all possible combinations of objects across the member classes.
Locate the member objects of the relationship you want to remove,
and uncheck the corresponding box in the table body.


Removing parameter definitions and values
=========================================

Using *Stacked tables*
~~~~~~~~~~~~~~~~~~~~~~

To remove parameter definitions or values,
go to the relevant *Stacked table* and select any cell in the row corresponding to the items
you want to remove
Then, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection and choose **Remove selected items** from the context menu.

Using *Pivot table*
~~~~~~~~~~~~~~~~~~~

To remove parameter definitions and/or values for a certain class,
bring the corresponding class to *Pivot table* using the **Parameter value** input type
(see :ref:`using_pivot_table_and_frozen_table`).
Then:

1. Select the cells in the *parameter* header corresponding to the parameter definitions you want to remove.
2. Select the cells in the table body corresponding to the parameter values you want to remove.

Finally, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection in *Pivot table* and choose **Remove selected items** from the context menu.


Removing parameter value lists
==============================

To remove parameter value list or any of their values, just select the appropriate rows in *Parameter value list*.
Then, either select **Edit -> Remove selected items** from the menu bar,
or right-click on the selection and choose **Remove selected items** from the context menu.


Mass-removing items
===================

To remove all items of specific types, select **Edit -> Mass remove items** from the menu bar.
The *Mass remove items* dialog will pop up:

.. image:: img/mass_remove_items_dialog.png
   :align: center


Select the databases from where you want to remove the items under *Databases*,
and the type of items you want to remove under *Items*.
Then, press **Ok**.

