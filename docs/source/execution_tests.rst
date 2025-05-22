.. _Execution tests:

Execution Tests
===============

Toolbox contains *execution tests* that test entire workflows in headless mode.
The tests can be found in :literal:`<toolbox repository root>/execution_tests/`.
Execution tests are otherwise normal Toolbox projects
except that the project root directories contains a :literal:`execution_test.py` file.
The tests utilize the :literal:`pytest` package
so the test code is practically identical to any unit tests in Toolbox.

Executing the tests
~~~~~~~~~~~~~~~~~~~

Tests are run as a GitHub action whenever a branch is pushed to GitHub.
This process is configured by :literal:`<project root>/.github/workflows/executiontest_runner.yml`

To execute the tests manually, run :literal:`pytest execution_test/` in project's root.
