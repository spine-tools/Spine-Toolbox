.. |add_entities| image:: ../../../spinetoolbox/ui/resources/menu_icons/cube_plus.svg
   :width: 16
   :alt:
.. |commit| image:: ../../../spinetoolbox/ui/resources/menu_icons/check.svg
   :width: 16
   :alt:
.. |execute_selection| image:: ../../../spinetoolbox/ui/resources/menu_icons/play-circle-regular.svg
   :width: 16
   :alt:
.. |open_file| image:: ../../../spinetoolbox/ui/resources/menu_icons/folder-open-solid.svg
   :width: 16
   :alt:

.. _The Diet Problem:

****************
The Diet Problem
****************

In this tutorial, you will be guided through how to use an existing Spine Toolbox project
to solve the `Diet problem <https://github.com/Pyomo/pyomo-gallery/blob/main/diet/DietProblem.ipynb>`_
which is one of the use-case examples of the `Pyomo <https://pyomo.readthedocs.io/en/stable/>`_ optimization package for Python.

.. _Setting Up the Project:

Setting Up the Project
======================

The Spine Toolbox project is available `in this GitHub repository <https://github.com/spine-tools/Diet-problem-demo>`_.
Download the project as a ZIP file and unzip it into whatever location you fancy.
Alternatively, you can clone the repository if you have Git installed.

We also need to create a Python environment with Pyomo, the HiGHS solver and :literal:`spinedb_api` installed.
:literal:`spinedb_api` will be used to read the input data and to write the results to the output database.

Start by opening a command prompt and :command:`cd` to the :literal:`Diet-problem-demo/` directory.

Create a Python virtual environment called :literal:`.venv` into :literal:`Diet-problem-demo/` and activate it.
Refer to the `venv Guide <https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/>`_
on how to do it as the exact commands depend on your system
and the Python version you are using.

After activating the environment, install :literal:`pyomo`, :literal:`highspy` and :literal:`spinedb_api` with::

   pip install pyomo highspy spinedb_api

.. note::

   If you feel like something is not working or you just want to restart from the beginning,
   feel free to delete the project directory and unzip the repository again.
   You can even keep multiple copies of the project directory around
   as they will all be treated as separate projects.

We have now finished all preparations outside of Spine Toolbox.
It is time to get to the real bread and butter of this tutorial.

Opening the Project in Toolbox
==============================

Start Spine Toolbox.

After taking a moment to marvel the Toolbox main window,
head to :menuselection:`File --> Open project...` or hit :kbd:`Ctrl+O`
which opens the **Open project** dialog.
Using the dialog, browse to the directory where you unzipped (or cloned) the demo project
and select :literal:`Diet-problem-demo`.
Click :guilabel:`OK` or hit :kbd:`Enter` to accept the selection.

In some cases, Toolbox may ask if you want to upgrade the project.
If this happens, answer :guilabel:`Yes` to the dialog.

You should see the workflow appear on **Design View** at the center of the main window.
Check that the **Event Log** in the lower left corner does not show any errors or warnings
to ensure that you are ready to proceed.

Taking a Tour of the Project
============================

The project consists of six project items.
They are, from left-to-right: Input data, Import input, Model, Solver and Results.
The yellow link arrows show the direction of the "flow" of the workflow
while the numbers on the top right corners of the project items
show the execution order.

The two Data Store items, Model and Results, have a red exclamation mark on their top left corners.
They are signs of problems.
Hovering the mouse pointer over the exclamation marks shows a tool tip that explains the issue:
the Data Stores point to non-existent databases.
We will fix this problem later.

As you may have gathered already, Spine Toolbox projects are in fact directories,
not files like in some image manipulation or spreadsheet software.
Let's see what makes a directory a Toolbox project.
**Right-click** the background of the **Design View**
and select :menuselection:`Open project directory...` from the context menu that pops up.
The action should open the project directory in the system's file manager.
You should see some files in the root of the directory like :file:`diet.py` and :file:`Foods and nutrients.xlsx`.
There should also be a :file:`.venv/` directory which contains the Python environment you created previously.

The idea of the project directory is that you can store all input files, scripts, documentation
and whatever is needed by the project in a single place.
Such projects are self-contained.
They can be easily moved around the file system, duplicated and shared with other people,
just like the current Diet problem project.

What makes a directory a Toolbox project, then?
The answer is the :file:`.spinetoolbox/` directory that contains a :file:`project.json` file.
The directory may also contain an :file:`items/` directory that holds project item specific files,
a :file:`local` directory that contains local settings,
a :file:`specifications` directory that contains reusable project item specifications
and perhaps backups of :file:`project.json`.

You can now close the file manager.
Next, we will have a look at the project settings and make some changes there.

Switching to Consumer Mode
==========================

Navigate to :menuselection:`File --> Project settings...` which opens the **Project settings** dialog.
The dialog contains some project-wide settings,
including project description
and an option to delete temporary files from the items directory in :file:`<project root>/.spinetoolbox/items`.

Since our intention is to use the project to solve the Diet problem
and not to develop it,
you should switch from **Author mode** to **Consumer mode**.
This will prevent any changes to :file:`<project root>/.spinetoolbox/project.json`.
However, certain changes will still get saved to the :file:`<project root>/.spinetoolbox/local/` directory
which is not under version control by Git.

Accept the changes in the dialog by clicking :guilabel:`OK` or by pressing :kbd:`Enter`.
Save the project by navigating to :menuselection:`File -> Save project` or by pressing :kbd:`Ctrl+S`.

.. _Creating Input and Output Databases:

Creating Input and Output Databases
===================================

Let's deal with the exclamation marks on the Model and Results Data Stores.
Click on the Model item to select it.
Its properties should appear on the item properties tab on the right side of the Toolbox window.
The item has already a database URL set to it.
Note, that **Dialect** is set to sqlite which is a file-backed SQL database.
The file itself is not included in the project directory so we need to create it.

Click :guilabel:`New Spine db` button on the lower left corner of the properties tab.
A **Create SQLite file** dialog opens.
Navigate to the :file:`<project root>/` directory
(the directory where the :file:`.spinetoolbox/` directory is)
if the dialog is displaying another path.
Check that the file name is :file:`Model.sqlite`
and accept the dialog by clicking :guilabel:`Save`.

The exclamation mark on the Model item should disappear
if the SQLite file was created successfully.

Follow the same procedure to fix the Results item.
This time around, the SQLite file should be called :file:`Results.sqlite`.

Let's quickly check :file:`Model.sqlite` we just created.
Double-click the Model item on Design view to open Spine DB Editor.
Alternatively, you can select the item and click :guilabel:`Open editor...` on its properties tab.
We will use DB Editor later to make some changes to the input data and to check the results.
For now, it is enough to note that the DB Editor window is mostly empty
as there is no data in the database except for one thing:
the **Alternative** list on the upper right corner shows one item,
an alternative called Base.
This alternative is always present in freshly created databases
and we will be relying on its existence when we import the input data into the database.

You can now close the DB Editor.

.. _Checking Input Data:

Checking Input Data
===================

Let's have a look at what the input data looks like.
Click the Input data Data Connection to select it and to see its properties.

Data Connection items introduce external data to the workflow
by holding references to files, directories and database URLs.
The Input data item holds a single file path reference to :file:`<project root>/Foods and nutrients.xlsx`
as you can see in its properties tab.

Double-clicking the file path of :file:`Foods and nutrients.xlsx` in the properties tab
should open the file in your spreadsheet application.
The file has three sheets: Foods, Nutrients and Nutrient content.
The Foods sheet contains a table that lists all foods and their costs and volumes per portion.
The Nutrients sheet contains different nutrients and their daily consumption limits.
The third sheet, Nutrient content, tabulates the nutritional content of each food.
This is our starting data.

You can now close the spreadsheet and focus back to Spine Toolbox.

.. _Basics of Spine Data Model:

Basics of Spine Data Model
==========================

We need import :file:`Foods and nutrients.xlsx` into the input Spine database.
Before doing that,
we need to understand some basics of Spine data model
so we can create the necessary transformation mappings from the tabular source data to the graph-like Spine data.

The most fundamental building block of Spine data is the entity class.
Entity classes represent different categories of data,
e.g. physical objects like foods and nutrients
or relationships between the objects like the nutritional content of foods.
A relationship class is said to have as many dimensions as the number of classes it connects
while a class representing objects is said to have zero dimensions.
The concrete instances of objects and relationships are called entities.
For example, a Food class could have an entity called cheeseburger.

Entity classes have parameter definitions
which determine the set parameters an entity of each class can have.
The concrete values for the parameter are defined for each entity.

Another important building block of Spine data is alternatives.
Basically, alternatives are named dimensions.
Every parameter value belongs to an alternative
which allows multiple instances of a single value to be present in the data.
Conversely, a parameter has at least one alternative value.
There could, for example, be a parameter called cost
which has two different values in alternatives called low inflation and high inflation.
As we saw in :ref:`Checking Input Data`,
our input database already has one alternative, Base.

Another use case for alternatives is entity activity control
which allows entities to be turned visible or invisible.
Unlike parameter values,
which all belong to an alternative,
entity alternatives are entirely optional.
An entity may have its activity defined for some alternatives or none.
In the latter case the activity of an entity is declared by a default activity set in its entity class.

Where this all comes together is when alternatives are used in building scenarios.
A scenario in Spine data is an ordered list of alternatives.
It captures a particular instance from the entity and parameter value space defined by alternatives.
The first alternative in the list of scenario’s alternatives is regarded as the lowest ranking
while the last as highest ranking.
A higher-ranking alternative overrides the lower ranking ones.
If a parameter has values in multiple alternatives,
only the one in the highest-ranking alternative will be available in a scenario.
Similarly, if an entity has activity defined for any of the alternatives in a scenario,
the highest-ranking activity wins.
For a more comprehensive treatment, see :ref:`Scenarios and alternatives` in Toolbox User Guide.

There are many more aspects to Spine data model.
However, the above introduction should be enough to get through this tutorial.

.. _Setting Up Import Mappings:

Setting Up Import Mappings
==========================

Now that we have basic understanding on what Spine data looks like,
let's see how to map the tables from :file:`Foods and nutrients.xlsx` into the input database.

Double-click the Import input item to open **Importer specification editor**.
This is where the mapping or transformation from the input file to Spine data is configured.
In fact, the mappings already exist
so you could just execute the Importer to write the contents of the file into the input database.
However, for the sake of this tutorial,
we will delete one of the mappings
and recreate it from scratch.

Remember, that if you run into trouble,
you can use undo (:kbd:`Ctrl+Z`) to restore the specification editor into a previous state.
A redo (:kbd:`Ctrl+Y`) action is also available.
In case of serious trouble, just close the editor without saving changes
and reopen it by double-clicking the icon of Import input.

At the top of the Importer specification editor window,
there is a **Name** and a **Description** field which are already filled.
Every specification must have at least a name.

On the left-hand side of Importer specification editor window,
you can see a list of tables that are available in the input.
These correspond to the sheets of :file:`Foods and nutrients.xlsx`.
All tables are checked on the list meaning that all of them will be imported.
Select (but don't change the check mark) the Foods table if not already selected.
A preview of the table is shown in the center of the window.
The colors in the table are a cue on which columns are mapped to which elements of Spine data model.
We will get back to that later.

The panels where the actual mappings are defined are on the right-hand side.
The specification currently has a single mapping, called foods, for the Foods table,
although there could be more depending on how much data the table holds.
Select foods from the **Mappings** list
and click the :guilabel:`Remove` button below the list.
Then, click :guilabel:`Add` to make a new one.
The new mapping is called Mapping (1) which is not very descriptive.
Double-click its name on the **Mappings** list to rename it e.g. to :literal:`foods` as it was previously.

What is the natural way to map the data in :file:`Foods and nutrients.xlsx` into Spine data?
We clearly have two separate categories: foods and nutrients,
which hints that we should have corresponding entity classes, Food and Nutrient, as well.
The categories are also linked together via the Nutrient content table in :file:`Foods and nutrients.xlsx`
which means we also need an entity class to describe that relationship.

The Foods table contains the different foods.
They will be the entities in the Food entity class.
Each food has two parameters, cost and volume,
meaning we need two parameter definitions for the Food entity class.

Before diving into how we map the table,
we should ensure the table is read correctly.
Have a look at the table-specific settings at the top of the preview table.
The :guilabel:`Has header` check box should be already checked.
You can uncheck and recheck it again to see how the preview changes accordingly.
Leave the checkbox checked.

Next, we must decide what we actually map with the current mapping.
Check that Entity class is selected in the :guilabel:`Item type` combo box on the right side of the window.
This means that we are mapping entity classes, entities and parameters.
The combo box contains a number of other item types
such as alternatives and scenarios that could be mapped from the table.

Since the table contains also cost and volume parameter values,
select Value from the :guilabel:`Parameter type` combo box.
The values are just plain numbers, so leave Single value selected on the :guilabel:`Value` combo box.
The other options allow importing multidimensional values like time series.

Leave the other options as-is.
They are useful in more complex mapping schemes.

At the bottom right corner there is a table that actually defines how table rows, columns and other elements map to Spine data.
It is here where the magic happens.
The first row in the table where Target is Entity class names
defines which table element maps to the entity class name.
Select Column Header from the Source type combo box.
Column Header means that we read the class name from the header of a specific column.
In case of the Foods table, this is the header of the first column
as you can see from the preview table.
This column must be referred to by Source ref. in the mappings table
which should already contain the correct value of 1.

Next, we need to set the mappings such that the entities are imported from the first column below the Food header.
Select the Source ref. cell on the Entity names row in the mappings table.
Type :literal:`1` in the cell and accept the edit by hitting :kbd:`Enter`.
The specification editor will automatically guess that you want to map column number 1 to Entity names
and changes the Source type accordingly.
Consequently, the Source type for Entity names should now be Column.
This should also be apparent on the preview table:
the Food column now has the same background color as the Entity names cell on the mappings table.

Now we have defined rules on how to read the entity class and its entities from the table.
Next, we need to deal with the parameters.
We start by defining a target alternative for the parameter values.
On the mappings table, select the Source ref. cell on the Alternative names row,
then type :literal:`Base` on it and press enter to accept the edit.
Note, that Source type for the row automatically changes to Constant
which means that all parameter values will be imported to a fixed alternative called Base.
You may recall that the target database, even though otherwise empty,
already contains the Base alternative
so we do not need to import or create it explicitly.

The parameter names for Food, cost and volume, can be found in the header.
We could import these parameters column-by-column using the same Column Header Source type
we used for Entity class names.
However, this would require a separate mapping for each parameter.
A more convenient way is to declare that the rest of the columns in the table contain parameter values.
To achieve this, set the Source type for Parameter names to Headers
which means that the rest of the headers after the first header will be treated as parameter names.
Doing this will trigger a number of automatic changes in the mappings table:
Firstly, Source ref. of Parameter names will be set to Headers.
Secondly, Source type of Parameter values will be set to Pivoted
and Source ref. will be set to Pivoted values.
Compare the new colors on the preview table to the mappings table.
The parameter values should now have the same background color as the Parameter values Target on the mappings table.
As all the column on the right of the Food column are now treated as containing parameters,
it would be possible to add any number of new parameters to the table
without the need to change the import mappings.

We still need to tell the Importer that the parameter values are numbers,
not strings or time stamps or whatever.
The data type of each column is marked in the header of the preview table.
Click on the button with the capital A on the left of the cost header.
A list of available data types pops up.
Select float from the list.
Note, that the icon on the button changes to the infinity sign denoting the new type.
Do the same change for the volume column.

We are done!
Save changes by pressing :kbd:`Ctrl+S` and close the specification editor.

.. _Importing Input Data:

Importing Input Data
====================

It is time to test put the Importer to test.
Select the Import input item on **Design view**
and click |execute_selection| :guilabel:`Selection` (or press :kbd:`F9`) on the **Execute** toolbar
at the top of the Toolbox main window.
The execution is handled by Spine Engine
which will communicate progress and messages back to Spine Toolbox.
You should see some animations on the Design view which indicate which item is being executed.
Also, an execution log gets printed on **Event log**.
After the execution finishes, a green sign should appear on the lower right corner of the icon of Import input.
If you see a red cross instead, then the execution was unsuccessful.
In any case, you should check what the item printed on **Event log**.
On a successful execution the important bit in the log is "Inserted 176 data with 0 errors".

If the execution failed, you probably made a mistake while setting up the import mappings.
Try repeating the process in :ref:`Setting Up Import Mappings`
or just close Toolbox, delete the project directory and start from scratch.

The input database should now contain the data from :file:`Foods and nutrients.xlsx`.

Working with Spine DB Editor
============================

We had a quick look at the Spine DB Editor in :ref:`Checking Input Data`.
Now, we will dive deeper into it.
Let's start by checking how the imported data looks like.

Open the editor by double-clicking the Model item.
This time around you should see a lot of data instead of the deserted views we had the first time we opened the editor.

On the left side is **Entity tree**
which shows the three entity classes we imported from :file:`Foods and nutrients.xlsx`:
Food, Nutrient and NutrientContent.
You can click the small arrow on the left of the classes to show their entities.
The small arrows next to the entities further expands the tree to show related entities,
that is, relationship entities the expanded entity is part of.

The center of the editor is occupied by four tabs of tables:
**Parameter value**, **Parameter definition**, **Entity alternative** and **Entity**.
Each table shows a table of corresponding data items.
The tables can be filtered by selection in **Entity tree**.
As an example of how the filtering works, switch to **Parameter definition** table
(by mouse or alternatively by :kbd:`Alt+Shift+3`),
then select Food in **Entity tree**.
The table should now show the cost and volume parameters
but it also shows the content parameter of the NutrientContent class.
Why?
Because the table shows also parameter definitions of related classes
and NutrientContent is a relationship class which has the Food class as one of its dimensions.
Selecting Nutrient on the **Entity tree** shows the parameter definitions of the Nutrient class instead.
This list also includes the content parameter of NutrientContent.
Filtering the tables by **Entity tree** selection is nice
but when combined with selections from the **Alternative** list and **Scenario tree**,
it becomes very powerful.

Next, let's have a look at the actual parameter values.
Switch to the **Parameter value** tab (:kbd:`Alt+3`).
First, make sure we see all values by right-clicking any cell in the table
and selecting :guilabel:`Clear all filters` from the popup menu.
Doing so clears the selection in **Entity tree**.
Take a moment to familiarize yourself with the table.
The group column is currently empty but it may be used to visually group related parameters in some datasets.
The class column shows the entity class, as one might expect.
Next to the class column is a column called entity byname.
It shows the name of the entity or a list of composing entity names if the entity is a relationship.
You can see this on the rows showing the parameter values of NutrientContent at the bottom of the table.
The name of the parameter is listed in the parameter name column,
while the alternative column says Base for all rows.
Finally, the actual value of the parameter is in the value column.

To see all parameter values associated with cheeseburgers,
select cheeseburger from **Entity tree**.
Holding down :kbd:`Ctrl` or :kbd:`Shift` during selection extends it.
Hold down :kbd:`Ctrl` and select fish sandwich.
You should now have both cheeseburger and fish sandwich selected
and the **Parameter value** table should be filtered accordingly.
Try out holding :kbd:`Shift` while extending the selection more.
Can you guess how its usage differs from holding :kbd:`Ctrl`?
Experiment as much as you like.

Adding Entity Classes, Entities, Parameters
===========================================

We are missing some data,
namely the constraint for the maximum volume of food a human being can consume daily.
For that we need to create a new entity class,
define a parameter for the class
and add an entity to the class that has a value for the parameter.
Remember that the Spine DB Editor has undo and redo functionality.
Feel free to use it if you think something went wrong.
In the extreme case, close the editor,
overwrite the database file with an empty database following the instructions in :ref:`Creating Input and Output Databases`
and rerun the Importer as described in :ref:`Importing Input Data`.

Let's start by creating the Constraint class.
Right-click the root element of **Entity tree**
and select :guilabel:`Add entity classes...` from the popup menu
which opens the **Add entity classes** dialog.
Write :literal:`Constraint` in the entity class name column
and click :guilabel:`OK` or hit :kbd:`Ctrl+Enter` to accept the dialog.
There should now be a class called Constraint in **Entity tree**.

Next, we need to add the maximum consumption parameter.
Select Constraint from **Entity tree** and switch to the **Parameter definition** table.
The table should be mostly empty as there are no parameters defined for the class.
The only row in the table has class readily set to Constraint.
This is a special row which is always present and is used to add new data to the table.
Select the parameter name cell and type :literal:`volume max` on it.
Pressing :kbd:`Enter` will accept the edit
and the parameter will be added as a new row in the table.

We need a Constraint entity to actually give a value to volume max.
In **Entity tree**, click the |add_entities| icon next to the Constraint class
which opens **Add entities** dialog.
Our model does not really care what the name of the entity is
but you can type :literal:`typical` to the entity name cell and accept the dialog.
Check that the entity got created by expanding the Constraint class in **Entity tree**
The entity should be in the list under Constraint.

Now that we have the entity,
we can create the value for volume max.
Select the entity called typical we just created in **Entity tree**
and switch to the **Parameter value** table.
The only row in the table should already be prefilled with the correct values for class and entity byname.
Double-click the parameter name cell and select the only option, volume max.
Do the same for alternative and select Base.
Finally, write :literal:`75` to value cell.
This will complete the row and we have a new parameter value.

At this point it is good to save our changes.
Click the |commit| :guilabel:`Commit` button on the toolbar (or press :kbd:`Ctrl+Enter`)
to commit your changes to the database.
You will be asked for a compulsory commit message.
If in doubt, write :literal:`Added volume max constraint.` to the message field
and accept the dialog by clicking the :guilabel:`Commit` button or by pressing :kbd:`Ctrl+Enter`.

Adding Alternatives
===================

Alternatives form the basis of scenarios of Spine data model as discussed in :ref:`Basics of Spine Data Model`.
Currently, the input database has only a single alternative, Base,
and all parameter values are in that alternative.
Entity activity control, on the other hand, requires entity alternatives which we do not have yet.

Let's start by introducing two new alternatives, expensive milk and no fries.
In the **Alternative** list, select the row below the Base alternative
where it says Type new alternative name here... and type :literal:`expensive milk`.
Accept the new alternative with :kbd:`Enter`.
Then add :literal:`no fries` the same way.

We want to give a higher price for milk in the expensive milk alternative.
Select lowfat milk from **Entity tree** under the Food class
and go to the **Parameter value** table.
On the mostly empty last row at the bottom of the table,
select the parameter name cell and press :kbd:`F2` to edit it.
Select cost from the list of parameter names using the :kbd:`Up` and :kbd:`Down` arrow keys
and press :kbd:`Tab` to proceed to edit the next cell.
Again, using :kbd:`Up` and :kbd:`Down`, select expensive milk from the list of alternatives
then press :kbd:`Tab` to proceed to the last cell.
Enter :literal:`1.2` to the value column and press :kbd:`Enter` to finish editing the row.
Now we have an alternative price for milk.
Cheese is also made of milk so let's adjust the price of cheeseburgers accordingly.
Select cheeseburger from **Entity tree**
and give it a new cost of :literal:`2.5` under the expensive milk alternative
following the same steps you did for lowfat milk.

Now that we have completed the expensive milk alternative,
let's turn our attention to entity activity control.
Switch to the **Entity alternative** table (:kbd:`Alt+4`).
The table is currently empty
which means that the activity of all of our entities depends on the default activity set for their classes.
We have not modified the default activities so all entities are always visible.
That will change that now.
Select fries under the Food class in **Entity tree**,
then double-click the alternative cell on the single row in the **Entity alternative** table.
Select no fries from the popup list.
Next, double-click the cell in the column called active
and select false.
Fries are now inactive and hidden in the no fries alternative.

Building Scenarios
==================

Having finished with the alternatives,
we will move on to building scenarios from them.

First, we need a baseline scenario.
On **Scenario tree** right below the **Alternative** list,
select the row that states Type new scenario name here...
and type :literal:`Baseline`.
After accepting the scenario name with :kbd:`Enter`,
expand the contents of the scenario with the small arrow on the left of its name.
Currently, the scenario is empty
and the only row in the expanded scenario says Type scenario alternative name here...
Type :literal:`Base` on the row and press :kbd:`Enter`.
We have our first scenario!

Add another scenario named Milk crisis.
Add the Base alternative to the scenario the same way you did with Baseline.
Then, add the expensive milk alternative to it as well.

Let's make a third scenario to showcase entity activity.
The new scenario is called Fryless bliss and it contains the Base and no fries alternatives.
Add it now.

Switch to the **Entity** table (:kbd:`Alt+5`) to see how entity activity works in practice.
Select Baseline from **Scenario tree**.
The table now displays all entities that are active in the scenario.
Notice, that fries are included in the table.
Next, select Fryless bliss from **Scenario tree**.
As you do this, fries disappear from the table.
This is a nice way to check if your entity activities are set correctly.

We are now done with the input database.
Commit your changes with a descriptive commit message
and close the editor.

Selecting Scenarios for Execution
=================================

Back in the **Design view** of Spine Toolbox,
select the yellow arrow that connects Model to Solver.
In the **Link properties** tab on the right,
there is now a list of the scenarios we just added to the input database.
You could pick just some of them for execution here.
However, we are going to run all of them,
so make sure they are all checked.

Setting up Model
================

Let's have a look at what the model looks like.
We must also set the correct Python environment for it.
For starters, double-click the Solver icon on **Design view** to open **Tool specification editor**.
The editor has some common elements with the **Importer specification editor**
we used in :ref:`Setting Up Import Mappings`.
At the top of the editor window, you can find the :guilabel:`Name` and :guilabel:`Description` fields.
The :guilabel:`Tool type` is set to Python as the Tool is actually a Python script.
On the left side there is a list of program files.
This Tool has only one file, :file:`diet.py`.
Most of the specification editor window is occupied by a code editor
which should currently show the contents of :file:`diet.py`.

As a rough overview of :file:`diet.py`,
the script first builds an abstract version of the Pyomo model for the diet problem.
From around line 35 onwards, we use :literal:`spinedb_api`,
a Python package to access, modify and manage Spine data,
to read the input database.
At line 82, we turn the abstract model into a concrete model instance
by feeding the input data to it.
Then we solve the model using the HiGHS solver.
Lastly, starting from line 86, we write the results back to the output database.

The URLs of input and output databases are given to the script as command line arguments.

Note, that the script has now notion of scenarios or alternatives.
Spine Engine and `spinedb_api` together ensure that the script "sees" only
relevant data when it reads the input database.

The script depends on :literal:`pyomo` and :literal:`spinedb_api` packages
which we installed into the :literal:`.venv` virtual environment in :ref:`Setting Up the Project`.
We need to set the Tool to use that environment when we execute it.
Click the |open_file| button on the left of :guilabel:`Interpreter` to open a file dialog.
The exact location of the Python interpreter in the :literal:`.venv` environment depends on your system,
but if you are on Windows, browse to :file:`<project root>/.venv/Scripts` and select :file:`python.exe`.

Press :kbd:`Ctrl+S` to save the specification and close the editor.

Solving the Model
=================

It is time to optimize the diet problem.
Select the Solver item
and hit the |execute_selection| :guilabel:`Selection` button on the **Execute** toolbar.

Spine Engine will start processing the selected item.
Since we have three scenarios to run,
it will create three work directories, one for each scenario
and spawn three Python processes so the solves can be executed in parallel.
In the **Event log**,
you should see a box for each scenario logging the progress.
Also, the **Console** dock should list three Executions.

The execution should take just a few seconds.
If successful, the Solver item should be marked as successfully executed,
and **Event log** will state "Executing Tool Solver finished" for each scenario
and "DAG 1/1 completed successfully" for the entire workflow.
If unsuccessful (the Solver item has a red cross and there is some red text in **Event log**),
check the consoles as they may give a hint what went wrong.
Common problems are the :literal:`.venv` environment
which may not be set correctly
or there is some issue with input data such as a typo in the volume max parameter.

The Python Consoles are userful for post-mortem debugging
as you can use them to interrogate the model.
For example, type :literal:`instance.c["cheeseburger"]` in any of the consoles
to see the cost of cheeseburgers the model was using.
Verify that the cost is higher in the Milk crisis scenario.

Analyzing the Results
=====================

It is time to check the fruits of our labor.
Double-click the Results Data Store to open Spine DB Editor.
Notice, that the database contains multiple alternatives,
names of which consist of the scenario name, the Tool name and an execution time stamp.
Go to the **Parameter value** table to view the results.
You can select any of the alternatives in the **Alternative** list
to see the results for that specific scenario and execution.
You can use :kbd:`Ctrl` to extend the selection
if you want to compare the results between scenarios or executions.

The value column in the **Parameter value** table says Map for all rows.
Map is a Spine-specific dataframe-like multidimensional data container.
Double-clicking any of the Maps in the table opens a value editor
which shows you a table of the daily quantities of each food that the optimal solution recommends.
Click :kbd:`Cancel` to close the editor without making any changes.

Right-click any of the Maps and select :guilabel:`Plot...` from the popup menu.
This opens a plot window which lets you visualize the daily quantities.
Right-clicking any other Map and selecting :guilabel:`Plot in window --> value`
adds that Map to the existing plot for comparison.
You can also select multiple Maps by holding :kbd:`Ctrl` or :kbd:`Shift`
before plotting.

Compare the results of the different scenarios
using different selections from **Alternative** list to filter the visible parameter values
and plotting multiple Maps on the same plot window.
How does the price of milk affect the recommended daily dosage of cheeseburgers?
How about orange juice?
How is the situation different if fries were never invented?

And that is it.
Congratulations, you have finished this tutorial!
