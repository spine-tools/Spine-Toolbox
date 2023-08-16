.. _Project item development:

Project Item Development
========================

This document discusses the basics of :ref:`project item<Project Items>` development:
what is required make one, how items interact with the Toolbox GUI and how they are executed.

The core of every project item consists of two classes:
a *static* project item class which is responsible for integrating the item with the Toolbox GUI
and an *executable* class which does the item's 'thing' and exists only during execution in Spine Engine.
Some additional classes are needed for Toolbox to be able to instantiate project items
and to communicate with the user via the Toolbox GUI.

**Specifications** are a way to make the settings of an item portable across projects.
In a sense a specification is a template that can specialize an item for a specific purpose
such as a Tool that runs certain model with known inputs an outputs.
Items that support specifications need to implement some additional methods and classes.

Getting started
---------------

Probably the most convenient way to start developing a new project item is to work with a copy of some simple
project item. For example, View provides a good starting point.

Project items are mostly self-contained Python packages.
It is customary to structure the project item packages like the Toolbox itself: ``mvcmodels`` submodule for Qt's
models, ``ui`` module for automatically generated UI forms and ``widgets`` for widgets' business logic.
However, the only actual requirement is that Toolbox expects to find the item's factory and item info
classes in the package's root modules as well as an :mod:`executable_item` module.

Item info
---------

A subclass of :class:`spine_engine.project_item.project_item_info.ProjectItemInfo` must be found
in one of the root modules of an item's package.
It is used by Toolbox to query the *type* and *category* of an item.
Type identifies the project item while category is used by the Toolbox GUI to group project items with similar function.
Categories are currently fixed and can be checked from :mod:`spine_items.category`.

Item Factory
------------

The details of constructing a project item and related objects have been abstracted away from Toolbox
by a factory that must be provided by every project item in a root module of the item's package.
The factory is a subclass of :class:`spinetoolbox.project_item.project_item_factory.ProjectItemFactory`.
Note that methods in the factory
that deal with specifications need to be implemented only by items that support them.

Executable item
---------------

A project item must have a root module called :mod:`executable_item` that contains a class
named :class:`ExecutableItem` which is a subclass of
:class:`spine_engine.project_item.executable_item_base.ExecutableItemBase`
:class:`ExecutableItem` acts as an access point to Spine Engine and contains the item's execution logic.

Toolbox side project item
-------------------------

A project item must subclass :class:`spinetoolbox.project_item.project_item.ProjectItem`
and return the subclass in its factory's :meth:`item_class` method.
Also :meth:`make_item` must return an instance of this class.
This class forms the core of integrating the item with Toolbox.

Specifications
--------------

Items that support specifications need to subclass
:class:`spine_engine.project_item.project_item_specification_factory.ProjectItemSpecificationFactory`
which provides an access point to Toolbox and Spine Engine to generate specifications.
The factory must be called :class:`SpecificationFactory` and be placed in :mod:`specification_factory`
module under item package's root.
The specification itself should be a subclass of
:class:`spine_engine.project_item.project_item_specification.ProjectItemSpecification`.

Toolbox GUI integration
-----------------------

:meth:`ProjectItemFactory.icon` returns a URL to the item's icon resource.
This is the item's 'symbol' shown e.g. on the main toolbar of Toolbox.
It should not be confused with the actual icon on Design view
which in turn is a subclass of :class:`spinetoolbox.project_item.project_item_icon.ProjectItemIcon`
and is returned by :meth:`ProjectItemFactory.make_icon`.

When creating a new item on the Design view Toolbox shows the *Add item dialog* it gets from
:meth:`ProjectItemFactory.make_add_item_widget`.
Toolbox provides :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`
which is a general purpose widget for this purpose
though project items are free to implement their own widgets as needed.

Once the item is on the Design view, the main interaction with it goes through the properties widget which is created
by :meth:`ProjectItemFactory.make_properties_widget`.
The properties widget should have all controls needed to set up the item.

Saving and restoring project items
----------------------------------

Project items are saved in JSON format as part of the :literal:`project.json` file.
Item saving is handled by :meth:`ProjectItem.item_dict` which should return a JSON compatible :class:`dict` and
contain at least the information returned by the base class method.

File system paths are handled specifically during saving: all paths outside the project directory should be absolute
while the paths in the project directory should be relative. This is to enable self-contained projects which include
all needed files and can be easily transferred from system to system. As such, paths are saved as special dictionaries.
:func:`spine_engine.utils.serialization.serialize_path`, :func:`spine_engine.utils.serialization.serialize_url` and
:func:`spine_engine.utils.serialization.deserialize_path` help with dealing with the paths.

:meth:`ProjectItem.from_dict` is responsible for restoring a saved project item
from the dictionary. :meth:`ProjectItem.parse_item_dict` can help to deserialize
the basic data needed by the base class.

Passing data between items: resources
-------------------------------------

Project items share data by files or via databases. One item writes a file which is then read by another item.
**Project item resources** are used to communicate the URLs of these files and databases.

Resources are instances of the :class:`spine.engine.project_item.project_item_resource.ProjectItemResource` class.

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

+------------------+-------+-------------------------+----------------------------+
| Item             | Notes | Provides to predecessor | Provides to successor      |
+==================+=======+=========================+============================+
| Data Connection  | [#]_  | n/a                     | File URLs                  |
+------------------+-------+-------------------------+----------------------------+
| Data Store       | [#]_  | Database URL            | Database URL               |
+------------------+-------+-------------------------+----------------------------+
| Data Transformer | [#]_  | n/a                     | Database URL               |
+------------------+-------+-------------------------+----------------------------+
| Exporter         |       | n/a                     | File URLs                  |
+------------------+-------+-------------------------+----------------------------+
| Importer         |       | n/a                     | n/a                        |
+------------------+-------+-------------------------+----------------------------+
| Merger           |       | n/a                     | n/a                        |
+------------------+-------+-------------------------+----------------------------+
| Tool             | [#]_  | n/a                     | File URLs                  |
+------------------+-------+-------------------------+----------------------------+
| View             |       | n/a                     | n/a                        |
+------------------+-------+-------------------------+----------------------------+

.. [#] Data connection provides paths to local files.
.. [#] Data Store provides a database URL to direct successors and predecessors. Note, that this is the
   only project item that provides resources to it's predecessors.
.. [#] Data Transformer provides its predecessors' database URLs modified by transformation configuration
   embedded in the URL.
.. [#] Tool's output files are specified by a *Tool specification*.

The table below lists the resources that might be used by each item type during execution.

+------------------+-------+---------------------------+------------------------+
| Item             | Notes | Accepts from predecessor  | Accepts from successor |
+==================+=======+===========================+========================+
| Data Connection  |       | n/a                       | n/a                    |
+------------------+-------+---------------------------+------------------------+
| Data Store       |       | n/a                       | n/a                    |
+------------------+-------+---------------------------+------------------------+
| Data Transformer |       | Database URL              | n/a                    |
+------------------+-------+---------------------------+------------------------+
| Exporter         |       | Database URL              | n/a                    |
+------------------+-------+---------------------------+------------------------+
| Importer         | [#]_  | File URLs                 | Database URL           |
+------------------+-------+---------------------------+------------------------+
| Merger           |       | Database URL              | Database URL           |
+------------------+-------+---------------------------+------------------------+
| Tool             | [#]_  | File URLs, database URLs  | Database URLs          |
+------------------+-------+---------------------------+------------------------+
| View             |       | Database URLs             | n/a                    |
+------------------+-------+---------------------------+------------------------+

.. [#] Importer requires a database URL from its successor for writing the mapped data.
   This can be provided by a Data Store.
.. [#] *Tool specification* specifies tool's optional and required input files.
   Database URLs can be passed to the tool *program* via command line arguments but are
   otherwise ignored by the Tool project item. Currently, there is no mechanism to know if a URL is
   actually required by a tool *program*. For more information, see :ref:`Tool specification editor`.


Execution
---------

Spine Engine instantiates the executable items in a DAG before the execution starts.
Then, Engine declares forward and backward resources for each item
using :meth:`ExecutableItemBase.output_resources`.
During execution, :meth:`ExecutableItemBase.execute` is invoked with lists of available resources
if an item is selected for execution.
Otherwise, :meth:`ExecutableItemBase.exclude_execution` is called.
