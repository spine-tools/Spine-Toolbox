..  Case Study A5 tutorial using the Importer Functionality
    Created: 30.7.2021


.. |ds_icon| image:: img/project_item_icons/database.svg
            :width: 16
.. |tool_icon| image:: img/project_item_icons/hammer.svg
             :width: 16
.. |execute_selection| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-regular.svg
             :width: 16
.. |file-regular| image:: ../../spinetoolbox/ui/resources/file-regular.svg
             :width: 16
.. |importer_icon| image:: ../../spinetoolbox/ui/resources/project_item_icons/database-import.svg
             :width: 16
.. |dc_icon| image:: ../../spinetoolbox/ui/resources/project_item_icons/file-alt.svg
             :width: 16




*****************************************
Case Study A5 tutorial using the Importer
*****************************************

Welcome to this Spine Toolbox Case Study tutorial.
Case Study A5 is one of the Spine Project case studies designed to verify
Toolbox and Model capabilities.
To this end, it *reproduces* an already existing study about hydropower
on the `Skellefte river <https://en.wikipedia.org/wiki/Skellefte_River>`_,
which models one week of operation of the fifteen power stations
along the river.

This tutorial provides a step-by-step guide to run Case Study A5 on Spine Toolbox
and is organized as follows:

.. contents::
   :local:

Introduction
============

Model assumptions
-----------------
For each power station in the river, the following information is known:

- The capacity, or maximal electricity output. This datum also provides the maximal water discharge
  as per the efficiency curve (see next point).
- The efficiency curve, or conversion rate from water to electricity.
  In this study, a piece-wise linear efficiency with two segments is assumed.
  Moreover, this curve is monotonically decreasing, i.e., the efficiency in the first segment is strictly greater
  than the efficiency in the second segment.
- The maximal reservoir level (maximal amount of water that can be stored in the reservoir).
- The reservoir level at the beginning of the simulation period and at the end.
- The minimal amount of water that the plant must discharge at every hour.
  This is usually zero (except for one of the plants).
- The minimal amount of water that needs to be *spilled* at every hour.
  Spilled water does not go through the turbine and thus is not used for producing electricity;
  it just helps keeping the reservoir level at bay.
- The downstream plant, or next plant in the river course.
- The time that it takes for the water to reach the downstream plant.
  This time can be different depending on whether the water is discharged (goes through the turbine) or spilled.
- The local inflow, or amount of water that naturally enters the reservoir at every hour.
  In this study, it is assumed constant over the entire simulation period.
- The hourly average water discharge. It is assumed that before the beginning of the simulation,
  this amount of water has constantly been discharged at every hour.

The system is operated so as to maximize the total profit over the planning week,
while respecting capacity constraints, maximal reservoir level constrains, etc.
Hourly profit per plant is simply computed as the product of the electricity price and the production.

Modelling choices
-----------------
The model of the electric system is fairly simple, only two elements are needed:

- A common electricity node.
- A load unit that takes electricity from that node.

On the contrary, the model of the river system is more detailed.
Each power station in the river is modelled using the following elements:

- An upper water node, located at the entrance of the station.
- A lower water node, located at the exit of the station.
- A power plant unit, that discharges water from the upper node into the lower node,
  and feeds electricity produced in the process to the common electricity node.
- A spillway connection, that takes spilled water from the upper node and releases it to the downstream upper node.
- A discharge connection, that takes water from the lower node and releases it to the downstream upper node.

Below is a schematic of the model. For clarity, only the Rebnis station is presented in full detail:


.. image:: img/case_study_a5_schematic.png
   :align: center
   :scale: 50%


Guide
=====

Installing requirements
-----------------------

.. note:: This tutorial is written for latest `Spine Toolbox 
   <https://github.com/Spine-project/Spine-Toolbox/>`_ and `SpineOpt 
   <https://github.com/Spine-project/SpineOpt.jl>`_ master versions.

Follow the instructions `here <https://github.com/Spine-project/SpineOpt.jl#installation>`_ 
to install Spine Toolbox and SpineOpt in your system.

Creating a new project
----------------------
Each Spine Toolbox project resides in its own directory, where the user can
store data, programming scripts and other necessary material. The Toolbox
application also creates its own special subdirectory *.spinetoolbox*, for project
settings, etc.

To create a new project, select **File -> New project…** from Spine Toolbox main
menu. Browse to a location where you want to create the project and create a new
folder for it, e.g. ‘cs_a5_importer’, and then click **Select Folder**.

Configuring SpineOpt
____________________

#. To use SpineOpt in your project, you need to create a Tool specification
   for it. Click on the small arrow next to the Tool icon |tool_icon| (in the *Main* section of
   the tool bar), and press **New…** The *Tool specification editor* will popup:

   .. image:: img/edit_tool_specification_blank.png
         :align: center

#. Type ‘SpineOpt’ as the name of the specification and select ‘Julia’ as the
   tool type. Deselect *Execute in work directory*.
#. Press |file-regular| next to *Main program* file to create a new Julia file. Enter a file
   name, e.g. ‘run_spineopt.jl’, and click **Save**.
#. Back in the *Tool specification editor*, select the file you just created
   under *Main program file*. Then, enter the following text in the text editor to
   the right:

   .. code-block:: julia

      using SpineOpt

      run_spineopt(ARGS...)

   At this point, the form should be looking like this:

   .. image:: img/edit_tool_specification_spine_opt.png
         :align: center

#. Press **Ctrl+S** to save everything, then close the *Tool specification editor*.

Setting up a project
--------------------

#. Drag the Data Store icon |ds_icon| from the tool bar and drop it into the
   *Design View*. This will open the *Add Data Store* dialogue. Type ‘input’ as the Data
   Store name and click **Ok**.
#. Repeat the above procedure to create a Data Store called ‘output’.
#. Create a database for the ‘input’ Data Store:

  #. Select the `input` Data Store item in the *Design View* to show the *Data Store
     Properties* (on the right side of the window, usually).
  #. In *Data Store Properties*, select the *sqlite* dialect at the top, and click
     **New Spine db**.

#. Repeat the above procedure to create a database for the ‘output’ Data Store.
#. Click on the small arrow next to the Tool icon |tool_icon| and drag the
   ‘SpineOpt’ item from the drop-down menu into the *Design View*. This will open the
   Add *Tool dialogue*. Type ‘SpineOpt’ as the Tool name and click **Ok**.
#. Drag the Data Connection icon |dc_icon| from the tool bar and drop it into the
   Design View. This will open the *Add Data connection dialogue*. Type in ‘Data
   Connection’ and click on **Ok**.
#. To import the model of the planning problem into the Spine database, you need
   to create an *Import specification*. Create an *Import specification* by clicking
   on the small arrow next to the Importer item (in the Main section of the toolbar) and
   press **New**. The *Importer specification editor* will pop-up:
#. Type ‘Import Model’ as the name of the specification. Save the specification by 
   using **Ctrl+S** and close the window.
#. Drag the newly created Import Model Importer item icon |importer_icon| from the tool bar and
   drop it into the *Design View*. This will open the Add Importer dialogue. Type in
   ‘Import Model’ and click on **Ok**.

   .. note:: Each item in the *Design view* is equipped with three *connectors*
      (the small squares at the item boundaries).

#. Connect ‘Data Connection’ with ‘Import Model’ by first clicking on one of the
   Data Connection’s connectors and then on one of the Importer’s connectors.
#. Repeat the procedure to create a path from ‘Data Connection’ to ‘output’. Now the 
   project should look similar to this as shown below:

   .. image:: img/item_connections.png
         :align: center

#. Setup the arguments for the *SpineOpt* Tool:

  #. Select the *SpineOpt* Tool to show the *Tool Properties* (on the right side of
     the window, usually). You should see two elements listed below *Available
     resources*, ``{db_url@input}`` and ``{db_url@output}``.
  #. Drag the first resource, ``{db_url@input}``, and drop it in *Command line
     arguments*, just as shown in the image below.
  #. Drag the second resource, ``{db_url@output}``, and drop it right below the
     previous one. The panel should be now looking like this:

      .. image:: img/case_study_a5_spine_opt_tool_properties_cmdline_args.png
         :align: center

  #. Double-check that the *order* of the arguments is correct: first,
     ``{db_url@input}``, and second, ``{db_url@output}``. (You can drag and drop to
     reorganize them if needed.)

#. From the main menu, select **File -> Save project**.

Importing the model
-------------------


#. Download `the SpineOpt database template 
   <https://raw.githubusercontent.com/Spine-project/SpineOpt.jl/master/templates/spineopt_template.json>`_
   , `the data <https://raw.githubusercontent.com/Spine-project/Spine-Toolbox/master/docs/source/data/a5.xlsx>`_ and `the 
   accompanying mapping <https://raw.githubusercontent.com/Spine-project/Spine-Toolbox/master/docs/source/data/mapping_case_study_a5.json>`_
   (right click on the links, then select *Save link as...*).

#. Add a reference to the file containing the model.

  #. Select the *Data Connection item* in the *Design View* to show the *Data
     Connection properties* window (on the right side of the window usually).
  #. In *Data Connection Properties*, click on the plus icon and select the
     previously downloaded Excel file.
  #. Next, double click on the *Import model* in the *Design view*. A window called *Select
     connector* for *Import Model* will pop-up, select Excel and klick **OK**. Next, still in
     the *Importer specification editor*, click the alternatives icon in the top
     right and import the mappings previously downloaded. Finally, save by clicking
     **Ctrl+S** and exit the *Importer specification editor*.

Executing the workflow
----------------------

Importing raw data with the importer
____________________________________

Once the workflow is defined and source file is in place, the project is ready to 
import the data to the input database. While holding **Ctrl**, select *Data Connection*, *Import Model*, 
and *input*. Directly click the *Execute selection* button |execute_selection| on the tool bar.

You should see ‘Executing Selected Directed Acyclic Graphs’ printed in the *Event log* (on the lower left by 
default). SpineOpt output messages will appear in the *Process Log* panel in the middle.
After some processing, ‘DAG 1/1 completed successfully’ appears and the execution is complete.

Importing the SpineOpt database template
________________________________________

#. Select the *input* Data Store item in the Design View. Go to *Data Store Properties* and click on 
   **Open editor**. This will open the newly created database in the Spine DB editor, looking similar to this:

   .. image:: img/case_study_a5_spine_db_editor_import.png
      :align: center

   |

   .. note:: The *Spine DB editor* is a dedicated interface within Spine Toolbox
      for visualizing and managing Spine databases.

#. Press **Alt + F** to display the main menu, select File -> Import…, and then
   select the template file you previously downloaded. (Tip: Make sure you search for a folder with .json 
   ending.) The contents of that file will be imported into the current database, and you should 
   then see classes like ‘commodity’, ‘connection’ and ‘model’ under the root node in the *Object tree* (on
   the left) with colourful icons.
#. From the menu in the top right corner, select **Session -> Commit**. Enter ‘Import SpineOpt
   template’ as message in the popup dialogue and click **Commit**. Exit the Spine DB editor.

   .. note:: The SpineOpt template contains the fundamental object and relationship classes,
      as well as parameter definitions, that SpineOpt recognizes and expects.
      You can think of it as the *generic structure* of the model,
      as opposed to the *specific data* for a particular instance.
      In the remainder of this section, we will add that specific data for the Skellefte river.

Execute the model
_________________

Finally, the project is ready to be executed. Hold **Ctrl**, select *SpineOpt* and *output*. Directly 
click on Execute selection |execute_selection|.


Examining the results
---------------------

Select the output data store and open the Spine DB editor.

.. image:: img/case_study_a5_output.png
   :align: center

To checkout the flow on the electricity load (i.e., the total electricity production in the system),
go to *Object tree*, expand the ``unit`` object class,
and select ``electricity_load``, as illustrated in the picture above.
Next, go to *Relationship parameter value* and double-click the first cell under `value`.
The *Parameter value editor* will pop up. You should see something like this:


.. image:: img/case_study_a5_output_electricity_load_unit_flow.png
   :align: center