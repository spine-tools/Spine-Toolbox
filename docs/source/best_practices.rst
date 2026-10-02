.. _Best Practices:

**************
Best Practices
**************

.. _Sharing project as a Git repository:

Sharing Project as a Git Repository
===================================

`Git`_ is a version control system that is handy for sharing Spine Toolbox projects.
Just add a :literal:`.gitignore` file to the project root (more of that later),
turn the project directory into Git repository
and push the repository to the cloud.

.gitignore File
---------------

It is recommended to exclude user's local settings such as database credentials from the Git repository
by adding the following line to the :literal:`.gitignore` file::

   .spinetoolbox/local/

The item directories in :literal:`<project dir>/.spinetoolbox/items/` usually contain temporary
result files and/or logs, so you may want to exclude those directories as well.
Toolbox will recreate the required directories when the project is opened,
so they need not be in the repository.

If the item directories do not contain any static data such as SQLite databases
or files in the item directories of Data Connections,
it may make sense to exclude the entire :literal:`items/` directory with the following line in :literal:`.gitignore`::

   .spinetoolbox/items/

Authoring a Project
-------------------

Just make sure you are in *Author mode* (by default you are, see :ref:`Project Settings`) before saving the project,
then commit your changes and push.

"Consuming" a Shared Project
----------------------------

Usually, you try to avoid modifying any files in the repository
when working with a project someone else has authored.
This is to avoid merge conflicts when pulling latest changes to the project from Git.
Being in *Consumer mode* (see :ref:`Project Settings`) helps here:
in the mode, :literal:`project.json` file is never overwritten.

.. note::

   Consumer mode is still under development and it does not track all changes to the project.
   The untracked changes will be lost when the project is closed.

.. _Git: https://git-scm.com/
