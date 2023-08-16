.. _Execution tests:

Execution Tests
===============

Toolbox contains *execution tests* that test entire workflows in the headless mode.
The tests can be found in :literal:`<toolbox repository root>/execution_tests/`.
Execution tests are otherwise normal Toolbox projects
except that the project root directories contain :literal:`__init__.py` and :literal:`execution_test.py` files.
:literal:`__init__.py` makes the directory part of the execution test suite
while :literal:`execution_test.py` contains actual test code.
The tests utilize Python's :literal:`unittest` package
so the test code is practically identical to any unit tests in Toolbox.

Executing the tests
~~~~~~~~~~~~~~~~~~~

Tests are run as a GitHub action whenever a branch is pushed to GitHub.
This process is configured by :literal:`<project root>/.github/workflows/executiontest_runner.yml`

To execute the tests manually, run :literal:`python -munittest discover --pattern execution_test.py` in project's root.
