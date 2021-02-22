..  Case Study A5 tutorial
    Created: 18.6.2018


.. |ds_icon| image:: img/project_item_icons/database.svg
            :width: 16
.. |tool_icon| image:: img/project_item_icons/hammer.svg
             :width: 16
.. |execute_project| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
             :width: 16
.. |new| image:: ../../spinetoolbox/ui/resources/menu_icons/file.svg
             :width: 16
.. |save| image:: ../../spinetoolbox/ui/resources/menu_icons/save_solid.svg
             :width: 16


**********************
Case Study A5 tutorial
**********************

Welcome to Spine Toolbox's Case Study A5 tutorial.
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
------------

Model assumptions
=================

For each power station in the river, the following information is known:

- The capacity, or maximum electricity output. This datum also provides the maximum water discharge
  as per the efficiency curve (see next point).
- The efficiency curve, or conversion rate from water to electricity.
  In this study, a piece-wise linear efficiency with two segments is assumed.
  Moreover, this curve is monotonically decreasing, i.e., the efficiency in the first segment is strictly greater
  than the efficiency in the second segment.
- The maximum magazine level, or amount of water that can be stored in the reservoir.
- The magazine level at the beginning of the simulation period, and at the end.
- The minimum amount of water that the plant needs to discharge at every hour.
  This is usually zero (except for one of the plants).
- The minimum amount of water that needs to be *spilled* at every hour.
  Spilled water does not go through the turbine and thus does not serve to produce electricity;
  it just helps keeping the magazine level at bay.
- The downstream plant, or next plant in the river course.
- The time that it takes for the water to reach the downstream plant.
  This time can be different depending on whether the water is discharged (goes through the turbine) or spilled.
- The local inflow, or amount of water that naturally enters the reservoir at every hour.
  In this study, it is assumed constant over the entire simulation period.
- The hourly average water discharge. It is assumed that before the beginning of the simulation,
  this amount of water has constantly been discharged at every hour.

The system is operated so as to maximize total profit over the week,
while respecting capacity constraints, maximum magazine level constrains, and so on.
Hourly profit per plant is simply computed as the product of the electricity price and the production,
minus a penalty for changes on the water discharge in two consecutive hours.
This penalty is computed as the product of a constant penalty factor, common to all plants,
and the absolute value of the difference in discharge with respect to the previous hour.

Modelling choices
=================

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
-----

Installing requirements
=======================

.. note:: This tutorial is written for latest `Spine Toolbox 
   <https://github.com/Spine-project/Spine-Toolbox/>`_ and `SpineOpt 
   <https://github.com/Spine-project/SpineOpt.jl>`_ development versions.

Follow the instructions `here <https://github.com/Spine-project/SpineOpt.jl#installation>`_ 
to install Spine Toolbox and SpineOpt in your system.


Creating a new project
======================

Each Spine Toolbox project resides in its own directory, where the user 
can store data, programming scripts and other necessary material. 
The Toolbox application also creates its own special subdirectory `.spinetoolbox`, 
for project settings, etc.

To create a new project, select **File -> New project...** from Spine Toolbox main menu.
Browse to a location where you want to create the project and create a new folder for it,
called e.g. ‘Case Study A5’, and then click **Open**.


Configuring SpineOpt 
~~~~~~~~~~~~~~~~~~~~

#. To use SpineOpt in your project, you need to create a Tool specification for it.
   Click on the small arrow next to the Tool icon |tool_icon| (in the *Items* section of the tool bar),
   and select **Create new Tool Specification...** from the drop-down menu.
   The *Edit Tool Specification* form will popup:

   .. image:: img/edit_tool_specification_new_program_file.png
         :align: center

#. Type ‘SpineOpt’ as the name of the specification and select ‘Julia’ as the type.
   Unselect *Execute in work directory*. 

#. Click on |new| (marked in red in the image above) to create a new Julia file.
   Enter a file name, e.g. ‘run_spineopt.jl’, and click **Save**.

#. Back in the *Edit Tool Specification* form, you should now see a small text editor
   with the legend *Create main program file here...*
   Go ahead and enter the following text in it: 

   .. code-block:: julia

      using SpineOpt
      run_spineopt(ARGS...)

   At this point, the form should be looking similar to this:

   .. image:: img/edit_tool_specification_spine_opt.png
         :align: center

#. Click |save| (marked in red in the image above) to save the main program file,
   and then **Ok** to save the specification and leave the form.


Setting up project
==================

#. Drag the Data Store icon |ds_icon| from the tool bar and drop it into the 
   *Design View*. This will open the *Add Data Store* dialog. 
   Type ‘input’ as the Data Store name and click **Ok**.

#. Repeat the above procedure to create a Data Store called ‘output’.

#. Create a database for the ‘input‘ Data Store.

   #. Select the `input` Data Store item in the *Design View* to show the *Data Store Properties* 
      (on the right side of the window, usually).

   #. In *Data Store Properties*, select the *sqlite* dialect at the top, and hit **New Spine db**.

#. Repeat the above procedure to create a database for the ‘output’ Data Store.

#. Click on the small arrow next to the Tool icon |tool_icon| and drag the ‘SpineOpt’
   item from the drop-down menu into the *Design View*.
   This will open the *Add Tool* dialog. Type ‘SpineOpt’ as the Tool name and click **Ok**.

   .. note:: Each item in the *Design view* is equipped with three *connectors*
      (the small squares at the item boundaries).

#. Click on one of ‘input’ connectors and then on one of ‘SpineOpt’ connectors. 
   This will create a *connection* from the former to the latter.

#. Repeat the procedure to create a *connection* from `SpineOpt` to `output`. 
   It should look something like this:

   .. image:: img/case_study_a5_item_connections.png
      :align: center

#. Setup the arguments for the `SpineOpt` Tool.

   #. Select the `SpineOpt` Tool to show the *Tool Properties* (on the right side of the window, usually).
      You should see two elements listed under *Available resources*, ``{db_url@input}`` and ``{db_url@output}``.

   #. Drag the first resource, ``{db_url@input}``, and drop it in *Command line arguments*,
      just as shown in the image below.

      .. image:: img/case_study_a5_spine_opt_tool_properties.png
         :align: center

   #. Drag the second resource, ``{db_url@output}``, and drop it right below the previous one.
      The panel should be now looking like this:

      .. image:: img/case_study_a5_spine_opt_tool_properties_cmdline_args.png
         :align: center

   #. Double-check that the *order* of the arguments is correct: first, ``{db_url@input}``, and second, ``{db_url@output}``.

#. From the main menu, select **File -> Save project**.



Entering input data
===================

Importing the SpineOpt database template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Download `the SpineOpt database template 
   <https://raw.githubusercontent.com/Spine-project/SpineOpt.jl/master/data/spineopt_template.json>`_
   (right click on the link, then select *Save link as...*)

#. Select the `input` Data Store item in the *Design View*.

#. Go to *Data Store Properties* and hit **Open editor**. This will open 
   the newly created database in the *Spine DB editor*, looking similar to this:

   .. image:: img/case_study_a5_spine_db_editor_empty.png
      :align: center

   |

   .. note:: The *Spine DB editor* is a dedicated interface within Spine Toolbox
      for visualizing and managing Spine databases.

#. Press **Alt + F** to display the main menu, select **File -> Import...**,
   and then select the template file you previously downloaded. 
   The contents of that file will be imported into the current database,
   and you should then see classes like ‘commodity’, ‘connection’ and ‘model’ under 
   the root node in the *Object tree* (on the left).

#. From the main menu, select **Session -> Commit**.
   Enter ‘Import SpineOpt template’ as message in the popup dialog, and click **Commit**.

Creating objects
~~~~~~~~~~~~~~~~

#. To add power plants to the model, create objects of class ``unit`` as follows:

   a. Select the list of plant names from the text-box below
      and copy it to the clipboard (**Ctrl+C**):

      ::

        Rebnis_pwr_plant
        Sadva_pwr_plant
        Bergnäs_pwr_plant
        Slagnäs_pwr_plant
        Bastusel_pwr_plant
        Grytfors_pwr_plant
        Gallejaur_pwr_plant
        Vargfors_pwr_plant
        Rengård_pwr_plant
        Båtfors_pwr_plant
        Finnfors_pwr_plant
        Granfors_pwr_plant
        Krångfors_pwr_plant
        Selsfors_pwr_plant
        Kvistforsen_pwr_plant

   b. Go to *Object tree* (on the top left of the window, usually),
      right-click on ``unit`` and select **Add objects** from the context menu. This will
      open the *Add objects* dialog.

   c. Select the first cell under the **object name** column
      and press **Ctrl+V**. This will paste the list of plant names from the clipboard into that column;
      the **object class name** column will be filled automatically with ‘unit‘.
      The form should now be looking similar to this:

        .. image:: img/add_power_plant_units.png
          :align: center

   d. Click **Ok**.
   e. Back in the *Spine DB editor*, under *Object tree*, double click on ``unit``
      to confirm that the objects are effectively there.
   f. Commit changes with the message ‘Add power plants’.


#. To add discharge and spillway connections, create objects of class ``connection``
   with the following names:
   ::

     Rebnis_to_Bergnäs_disch
     Sadva_to_Bergnäs_disch
     Bergnäs_to_Slagnäs_disch
     Slagnäs_to_Bastusel_disch
     Bastusel_to_Grytfors_disch
     Grytfors_to_Gallejaur_disch
     Gallejaur_to_Vargfors_disch
     Vargfors_to_Rengård_disch
     Rengård_to_Båtfors_disch
     Båtfors_to_Finnfors_disch
     Finnfors_to_Granfors_disch
     Granfors_to_Krångfors_disch
     Krångfors_to_Selsfors_disch
     Selsfors_to_Kvistforsen_disch
     Kvistforsen_to_downstream_disch
     Rebnis_to_Bergnäs_spill
     Sadva_to_Bergnäs_spill
     Bergnäs_to_Slagnäs_spill
     Slagnäs_to_Bastusel_spill
     Bastusel_to_Grytfors_spill
     Grytfors_to_Gallejaur_spill
     Gallejaur_to_Vargfors_spill
     Vargfors_to_Rengård_spill
     Rengård_to_Båtfors_spill
     Båtfors_to_Finnfors_spill
     Finnfors_to_Granfors_spill
     Granfors_to_Krångfors_spill
     Krångfors_to_Selsfors_spill
     Selsfors_to_Kvistforsen_spill
     Kvistforsen_to_downstream_spill

#. To add water nodes, create objects of class ``node`` with the following names:

   ::

     Rebnis_upper
     Sadva_upper
     Bergnäs_upper
     Slagnäs_upper
     Bastusel_upper
     Grytfors_upper
     Gallejaur_upper
     Vargfors_upper
     Rengård_upper
     Båtfors_upper
     Finnfors_upper
     Granfors_upper
     Krångfors_upper
     Selsfors_upper
     Kvistforsen_upper
     Rebnis_lower
     Sadva_lower
     Bergnäs_lower
     Slagnäs_lower
     Bastusel_lower
     Grytfors_lower
     Gallejaur_lower
     Vargfors_lower
     Rengård_lower
     Båtfors_lower
     Finnfors_lower
     Granfors_lower
     Krångfors_lower
     Selsfors_lower
     Kvistforsen_lower

#. Next, create the following objects:

   a. ``instance`` of class ``model``.

   b. ``water`` and ``electricity`` of class ``commodity``.

   c. ``electricity_node`` of class ``node``.

   d. ``electricity_load`` of class ``unit``.

   e. ``some_week`` of class ``temporal_block``.

   f. ``deterministic`` of class ``stochastic_structure``.

   g. ``realization`` of class ``stochastic_scenario``.

#. Finally, create the following objects to get results back from Spine Opt:

   a. ``my_report`` of class ``report``.

   b. ``unit_flow``, ``connection_flow``, and ``node_state`` of class ``output``.



.. _Specifying object parameter values:

Specifying object parameter values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#. To specify the general behaviour of our model, enter ``model`` parameter values as follows:

   a. Select the model parameter value data from the text-box below
      and copy it to the clipboard (**Ctrl+C**):

      .. literalinclude:: data/cs-a5-model-parameter-values.txt

   b. Go to *Object parameter value* (on the top-center of the window, usually).
      Make sure that the columns in the table are ordered as follows:
      
      ::

         object_class_name | object_name | parameter_name | alternative_name | value | database

   c. Select the first empty cell under ``object_class_name`` and press **Ctrl+V**.
      This will paste the model parameter value data from the clipboard into the table.
      The form should be looking like this:

      .. image:: img/case_study_a5_model_parameters.png
            :align: center

#. To specify the resolution of our temporal block, repeat the same procedure with the data below:

   .. literalinclude:: data/cs-a5-temporal_block-parameter-values.txt

#. To specify the behaviour of all system nodes, repeat the same procedure with the data below, where:

   a. ``demand`` represents the local inflow (negative in most cases).
   b. ``fix_node_state`` represents fixed reservoir levels (at the beginning and the end).
   c. ``has_state`` indicates whether or not the node is a reservoir (true for all the upper nodes).
   d. ``state_coeff`` is the reservoir 'efficienty' (always 1, meaning that there aren't any loses).
   e. ``node_state_cap`` is the maximum level of the reservoirs.


   .. literalinclude:: data/cs-a5-node-parameter-values.txt



Establishing relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tip:: To enter the same text on several cells, copy the text into the clipboard, then select all
   target cells and press **Ctrl+V**.


#. To establish that (i) power plant units receive water from 
   the station's upper node, and (ii) the electricity load unit takes electricity from the common
   electricity node, create relationships of class ``unit__from_node`` as follows:

   a. Select the list of unit and node names from the text-box below
      and copy it to the clipboard (**Ctrl+C**).

      .. literalinclude:: data/cs-a5-unit__from_node.txt

   b. Go to *Relationship tree* (on the bottom left of the window, usually),
      right-click on ``unit__from_node``
      and select **Add relationships** from the context menu. This will
      open the *Add relationships* dialog.

   c. Select the first cell under the *unit* column
      and press **Ctrl+V**. This will paste the list of plant and node names from the clipboard into the table.
      The form should be looking like this:

      .. image:: img/add_pwr_plant_water_from_node.png
        :align: center

   d. Click **Ok**.
   e. Back in the *Spine DB editor*, under *Relationship tree*, double click on
      ``unit__from_node`` to confirm that the relationships are effectively there.
   f. From the main menu, select **Session -> Commit** to open the *Commit changes* dialog.
      Enter ‘Add from nodes of power plants‘ as the commit message and click **Commit**.

#. To establish that (i) power plant units release water to the station's lower node,
   and (ii) power plant units inject electricity to the common electricity node,
   create relationships of class ``unit__to_node`` with the following data:

   .. literalinclude:: data/cs-a5-unit__to_node.txt

   .. note:: At this point, you might be wondering what's the purpose of the ``unit__node__node``
      relationship class. Shouldn't it be enough to have ``unit__from_node`` and ``unit__to_node`` to represent
      the topology of the system? The answer is yes; but in addition to topology, we also need to represent
      the *conversion process* that happens in the unit, where the water from one node is turned into electricty
      for another node. And for this purpose, we use a relationship parameter value on the ``unit__node__node``
      relationships (see :ref:`Specifying relationship parameter values`).

#. To establish that (i) discharge connections take water from the *lower* node of the upstream station,
   and (ii) spillway connections take water from the *upper* node of the upstream station,
   create the following relationships of class ``connection__from_node``:

   .. literalinclude:: data/cs-a5-connection__from_node.txt

#. To establish that both discharge and spillway connections release water onto 
   the upper node of the downstream station, create the following ``connection__to_node`` relationships:

   .. literalinclude:: data/cs-a5-connection__to_node.txt

   .. note:: At this point, you might be wondering what's the purpose of the ``connection__node__node``
      relationship class. Shouldn't it be enough to have ``connection__from_node`` and ``connection__to_node``
      to represent the topology of the system? The answer is yes; but in addition to topology, we also need to represent
      the *delay* in the river branches.
      And for this purpose, we use a relationship parameter value on the ``connection__node__node``
      relationships (see :ref:`Specifying relationship parameter values`).


#. To establish that water nodes balance water and the electricity node balances 
   electricity, create ``node__commodity`` relationships between all upper and lower reservoir nodes 
   and the ``water`` commodity, as well as between the ``electricity_node`` and ``electricity``.

   .. literalinclude:: data/cs-a5-node__commodity.txt

#. Next, to establish that all nodes are balanced at each time slice in the one week horizon,
   create relationships of class ``model__default_temporal_block`` between the model ``instance`` 
   and the temporal_block ``some_week``.

#. To establish that this model is deterministic,
   create a relationships of class ``model__default_stochastic_structure`` between the model ``instance`` 
   and the temporal_block ``deterministic``, and a relationship of class ``stochastic_structure__stochastic_scenario``
   between ``deterministic`` and ``realization``.

#. Finally, create one relationship of class ``report__output`` between ``my_report`` and each of
   the following ``output`` objects: ``unit_flow``, ``connection_flow``, and ``node_state``, as well as
   one relationship of class ``model__report`` between ``instance`` and ``my_report``.
   This is so results from running Spine Opt are written to the ouput database.


.. _Specifying relationship parameter values:

Specifying relationship parameter values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#. To specify (i) the capacity of hydro power plants, 
   and (ii) the variable operating cost of the electricity unit (equal to the negative electricity price), enter ``unit__from_node`` parameter values as follows:

   a. Select the parameter value data from the text-box below
      and copy it to the clipboard (**Ctrl+C**):

      .. literalinclude:: data/cs-a5-unit__from_node-relationship-parameter-values.txt

   b. Go to *Relationship parameter value* (on the bottom-center of the window, usually).
      Make sure that the columns in the table are ordered as follows:

      ::

         relationship_class_name | object_name_list | parameter_name | alternative_name | value | database

   c. Select the first empty cell under ``relationship_class_name`` and press **Ctrl+V**.
      This will paste the parameter value data from the clipboard into the table.


#. To specify the conversion ratio from water to electricity and from water to water
   of different hydro power plants (the latter being equal to 1), repeat the same procedure with the data below:

   .. literalinclude:: data/cs-a5-unit__node__node-relationship-parameter-values.txt


#. To specify the average discharge and spillage in the first hours of the simulation,
   repeat the same procedure with the data below:

   .. literalinclude:: data/cs-a5-connection__from_node-relationship-parameter-values.txt


#. Finally, to specify the delay and transfer ratio of different water connections (the latter being equal to 1),
   repeat the same procedure with the data below:

   .. literalinclude:: data/cs-a5-connection__node__node-relationship-parameter-values.txt


#. When you're ready, commit all changes to the database.


Executing the workflow
======================

Once the workflow is defined and input data is in place, the project is ready
to be executed. Hit the **Execute project** button |execute_project| on 
the tool bar.

You should see ‘Executing All Directed Acyclic Graphs’ printed in the *Event log*
(on the lower left by default).
SpineOpt output messages will appear in the *Process Log* panel in the middle.
After some processing, ‘DAG 1/1 completed successfully’ appears and the 
execution is complete.


Examining the results
=====================

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