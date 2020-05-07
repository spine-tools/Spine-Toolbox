Project item development
========================

This document discusses the structure of :ref:`project items<Project Items>`,
how they interact with the Toolbox GUI and how they are executed.

The core of every project item consists of two classes:
a *static* project item class which is a subclass of :class:`spinetoolbox.project_item.ProjectItem`
and an *executable*, a subclass of :class:`spinetoolbox.executable_item.ExecutableItem`.
The static item is responsible for integrating the item with the Toolbox while
its executable counterpart exists only during execution.

There are several other classes assisting with integrating a project item to the Toolbox
in addition to the static project item class:

* The item's Design view icon which is inherited from :class:`spinetoolbox.graphics_items.ProjectItemIcon`.
* Properties tab widget and other UI widgets which are needed to change the item's settings.
  Currently, most of the properties widget's logic is actually in the static project item class.
* An *add project item* widget. Some project items use the general purpose
  :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`
  while others use more specialized widgets.

Storing and restoring items
---------------------------

Project items are serialized into JSON compatible Python dictionaries by
:func:`spinetoolbox.project_item.ProjectItem.item_dict`.
The dictionaries are structured such that they can be given to item's ``__init__()`` method directly as kwargs
in addition to the ``toolbox``, ``project`` and ``logger`` arguments.

Passing data between items: resources
-------------------------------------

Project items share data by files or via databases. One item writes a file which is then read by another item.
*Project item resources* are used to communicate the URLs of these files and databases.

Resources are instances of the :class:`spinetoolbox.project_item.ProjectItemResource` class.

Both static items and their executable counterparts pass resources.
The major difference is that static item's may pass resource *promises*
such as files that are generated during the execution.
The full path to the promised files or even their final names may not be known until the items are executed.

During execution resources are propagated only to item's *direct* predecessors and successors.
Static items offer their resources to direct successors only.
Resources that are communicated to successor items are basically output files
that the successor items can use for input.
Currently, the only resource that is propagated to predecessor items is database URLs by Data Store project items.
As Data Stores leave the responsibility of writing to the database to other items
it has to tell these items where to write their output data.

The table below lists the resources each project item type provides during execution.

+-----------------+-------+-------------------------+-----------------------+
| Item            | Notes | Provides to predecessor | Provides to successor |
+=================+=======+=========================+=======================+
| Data Connection | [#]_  | n/a                     | File URLs             |
+-----------------+-------+-------------------------+-----------------------+
| Data Store      | [#]_  | Database URL            | Database URL          |
+-----------------+-------+-------------------------+-----------------------+
| Exporter        |       | n/a                     | File URLs             |
+-----------------+-------+-------------------------+-----------------------+
| Importer        |       | n/a                     | n/a                   |
+-----------------+-------+-------------------------+-----------------------+
| Tool            | [#]_  | n/a                     | File URLs             |
+-----------------+-------+-------------------------+-----------------------+
| View            |       | n/a                     | n/a                   |
+-----------------+-------+-------------------------+-----------------------+

.. [#] Data connection provides paths to local files.
.. [#] Data Store provides a database URL to direct successors and predecessors. Note, that this is the
   only project item that provides resources to it's predecessors.
.. [#] Tool's output files are specified by a *Tool specification*.

The table below lists the resources that migh be used by each item type during execution.

+-----------------+-------+---------------------------+------------------------+
| Item            | Notes | Accepts from predecessor  | Accepts from successor |
+=================+=======+===========================+========================+
| Data Connection |       | n/a                       | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| Data Store      |       | n/a                       | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| Exporter        |       | Database URL              | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| Importer        | [#]_  | File URLs                 | Database URL           |
+-----------------+-------+---------------------------+------------------------+
| Tool            | [#]_  | File URLs, database URLs  | Database URLs          |
+-----------------+-------+---------------------------+------------------------+
| View            |       | Database URLs             | n/a                    |
+-----------------+-------+---------------------------+------------------------+

.. [#] Importer requires a database URL from its successor for writing the mapped data.
   This can be provided by a Data Store.
.. [#] *Tool specification* specifies tool's optional and required input files.
   Database URLs can be passed to the tool *program* via command line arguments but are
   otherwise ignored by the Tool project item. Currently, there is no mechanism to know if a URL is
   actually required by a tool *program*. For more information, see :ref:`Tool specification editor`.


Execution
---------

The executable counterparts for project items in a DAG are created before execution.
The current settings of each item are passed to the executable
which is then sent to Spine Engine for execution.

The DAG is executed in two phases: first backwards then forwards.
During backward execution, the DAG is executed in an inverted order
and resources are propagated to direct predecessors.
No current project item actually executes any other code besides storing these resources for later use.
Forward execution is when the project items do their actions.

When executing in either direction:

#. :func:`spinetoolbox.executable_item.ExecutableItem.execute` is invoked with a list of available resources
   and current execution direction.
#. The resources returned by :func:`spinetoolbox.executable_item.ExecutableItem.output_resources` are
   accumulated and passed to the ``execute()`` of the successor item.

The ``execute()`` method further delegates the exedution to the overridable
:func:`spinetoolbox.executable_item.ExecutableItem._execute_forward` and
:func:`spinetoolbox.executable_item.ExecutableItem._execute_backward` methods.
Similarly, ``output_resources()`` calls the
:func:`spinetoolbox_executable_item.ExecutableItem._output_resources_forward` and
:func:`spinetoolbox_executable_item.ExecutableItem._output_resources_backward` methods.

The executable items need additional properties to function.
The table below lists the properties for each item.
Basically, these are the arguments that are provided to each executable's ``__init__`` method.

+-----------------+-------+--------------------------+
| Item            | Notes | Properties               |
+=================+=======+==========================+
| Data Connection | [#]_  | File references          |
+                 +-------+--------------------------+
|                 | [#]_  | Data files               |
+-----------------+-------+--------------------------+
| Data Store      |       | Database URL             |
+-----------------+-------+--------------------------+
| Exporter        |       | Export settings          |
+                 +-------+--------------------------+
|                 |       | Output directory         |
+                 +-------+--------------------------+
|                 | [#]_  | GAMS system directory    |
+-----------------+-------+--------------------------+
| Importer        |       | Mapping settings         |
+                 +-------+--------------------------+
|                 |       | Log directory            |
+                 +-------+--------------------------+
|                 | [#]_  | Python system directory  |
+                 +-------+--------------------------+
|                 | [#]_  | GAMS system directory    |
+                 +-------+--------------------------+
|                 | [#]_  | Cancel on error flag     |
+-----------------+-------+--------------------------+
| Tool            |       | Work directory           |
+                 +-------+--------------------------+
|                 |       | Output directory         |
+                 +-------+--------------------------+
|                 |       | Tool specification       |
+                 +-------+--------------------------+
|                 |       | Command line arguments   |
+-----------------+-------+--------------------------+
| View            |       | n/a                      |
+-----------------+-------+--------------------------+

.. [#] Path to files which can be anywhere in the file system.
.. [#] Files which reside in the item's data directory.
.. [#] Path to the directory which contains a GAMS installation.
   Required to find the libraries needed for writing ``.gdx`` files.
.. [#] Path to the directory which contains a Python installation.
   Required to run the import operation in a separate process.
.. [#] Path to the directory which contains a GAMS installation.
   Required to find the libraries needed for reading ``.gdx`` files.
.. [#] A flag indicating if the import operation should stop when an error is encountered.
