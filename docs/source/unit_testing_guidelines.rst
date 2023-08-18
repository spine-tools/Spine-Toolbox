.. _Unit testing guidelines:

Unit Testing Guidelines
=======================

Test modules, directories
~~~~~~~~~~~~~~~~~~~~~~~~~

Spine project uses Python standard `unittest <https://docs.python.org/3/library/unittest.html>`_ framework for testing.
The tests are organized into Python modules starting with the prefix :literal:`test_`
under :literal:`<project root>/tests/`.
The structure of :literal:`tests/` mirrors that of the package being tested.
Note that all subdirectories containing test modules under :literal:`tests/` must have an (empty) :literal:`__init__.py`
which makes them part of the project's test package.

While there are no strict rules on how to name the individual test modules except for the :literal:`test_` prefix,
:literal:`test_<module_name>.py` is preferred.

Running the tests
~~~~~~~~~~~~~~~~~

Tests are run as a GitHub action whenever a branch is pushed to GitHub.
This process is configured by :literal:`<project root>/.github/workflows/unittest_runner.yml`

To execute the tests manually, run :literal:`python -munittest discover` in project's root.

Helpers
~~~~~~~

:literal:`mock_helpers` module in Toolbox's test package contains some helpful functions.
Especially the methods to create mock :literal:`ToolboxUI` and :literal:`SpineToolboxProject` objects come very handy.

When instantiation of :literal:`QWidget` (this includes all GUI testing) is needed,
Qt's main loop must be running during testing.
This can be achieved by e.g. the :literal:`setUpClass` method below:

.. code-block:: python

   @classmethod
   def setUpClass(cls):
       if not QApplication.instance():
           QApplication()

Sometimes an in-memory database can be handy because it does not require a temporary files or directories
and it may be faster than an :literal:`.sqlite` file.
To create an in-memory database, use :literal:`sqlite://` as the URL:

.. code-block:: python

   db_map = DiffDatabaseMapping("sqlite://", create=True)

Unfortunately, it is not possible to refer to the created database with the same URL
prohibiting multiple database maps the access to the same in-memory database.
