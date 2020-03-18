Project item development
========================

This document discusses the structure of project items, how they interact with the Toolbox GUI
and how they are executed.

Project items consist of several parts:

* Most of the logic is in a *main project item class* which is a subclass of
  :class:`spinetoolbox.project_item.ProjectItem`.
* The item's Design view icon is inherited from :class:`spinetoolbox.graphics_items.ProjectItemIcon`.
* Properties tab widget and other widgets are needed for user interaction.
  Currently, most of the properties widget's logic is actually in the main project item class.
* An *add project item* widget. Some project items use the general purpose
  :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`
  while others use more specialized widgets.

In principle only the main project item class is needed for execution.

Storing and restoring items
---------------------------

Project items can be serialized into Python dictionaries by ``spinetoolbox.project_item.ProjectItem.item_dict``.
The dictionaries are structured such that they can be given to item's ``__init__`` method directly as kwargs
in addition to the ``toolbox``, ``project`` and ``logger`` arguments.

Static and dynamic states
-------------------------

It is important to note that the project items live a sort of dual life:
a 'static' state in which they are shown on the Design view allowing users to edit their properties,
make and break connections etc.
and a 'dynamic' state when the DAG is executed.

Passing data between items: resources
-------------------------------------

Project items share data by files or databases. One item writes a file which is then read by another item.
*Project item resources* are used to communicate the URLs of these files and databases.

Resources are objects of the :class:`spinetoolbox.project_item.ProjectItemResource` class.

Resources are propagated only to item's direct predecessor and successor items.
Resources that are communicated to the successor items are basically output files
that the successor items can use for input.
Currently, the only resource that is propagated to predecessor items is database URLs by Data Store project items.
As Data Stores leave the responsibility of writing to the database to other items
it has to tell these items where to write their output data.

Execution
---------

The DAG is executed in two phases: first backwards then forwards.
During backward execution, the DAG is executed in an inverted order
and resources are propagated to items' direct predecessors.
No current project item actually executes any other code besides handling these resources.
Forward execution is when the project items do their actions.

When executing in either direction:

#. :func:`spinetoolbox.project_item.ProjectItem.execute` is invoked with a list of available resources
   and current execution direction.
#. The resources returned by :func:`spinetoolbox.project_item.ProjectItem.output_resources` are
   accumulated and passed to the proceeding item's ``execute()``.

These are the methods taking part in the execution:

:func:`spinetoolbox.project_item.ProjectItem.execute`
   Delegates the execution and resources from direct predecessors and successors to either one of the following
   functions depending on ``direction``.

:func:`spinetoolbox.project_item.ProjectItem.execute_backward`
   This method is called when the DAG is executed backwards. At the moment, most items do nothing here.
   The ones that do store database URLs from direct successor Data Stores for later use.
:func:`spinetoolbox.project_item.ProjectItem.execute_forward`
   Executes the item's actual action.

These methods are used to collect resources during execution:

:func:`spinetoolbox.project_item.ProjectItem.output_resources`
   Delegates resource gathering to one of the following methods depending on ``direction``.
:func:`spinetoolbox.project_item.ProjectItem.output_resources_backward`
   Returns item's resources that are meant to be seen by the item's direct predecessors.
:func:`spinetoolbox.project_item.ProjectItem.output_resources_forward`
   Returns item's resoruces that are meant to be seen by the item's direct successors.
