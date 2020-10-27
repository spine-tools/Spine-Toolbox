..  Case Study A5 tutorial
    Created: 18.6.2018


.. |ds_icon| image:: ../../spinetoolbox/ui/resources/project_item_icons/database.svg
            :width: 16
.. |tool_icon| image:: ../../spinetoolbox/ui/resources/project_item_icons/hammer.svg
             :width: 16
.. |execute_project| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-solid.svg
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
- A reservoir unit, that takes water from the upper node to put it into a water storage and viceversa.
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

.. note:: This tutorial is written for Spine Toolbox `version 0.5 
   <https://github.com/Spine-project/Spine-Toolbox/tree/release-0.5>`_. 

Make sure that Spine Toolbox version 0.5 and Julia 1.2 (or greater) are properly 
installed as described at the following links:

- `Running Spine Toolbox <https://github.com/Spine-project/Spine-Toolbox#running-spine-toolbox>`_
- `Julia downloads <https://julialang.org/downloads/>`_


Setting up project
==================

Each Spine Toolbox project resides in its own directory. In this directory the user 
can collect all data, programming scripts and other material needed for the project. 
The Toolbox application also creates its own special subdirectory `.spinetoolbox`, 
for project settings etc.

#. Launch Spine Toolbox and from the main menu, select **File -> New project...** 
   to create a new project. Browse to a location where you want to create the project
   and create a new folder for it, e.g. ‘Case Study A5’.

#. Drag the Data Store icon (|ds_icon|) from the toolbar and drop it into the 
   *Design View*. This will open the *Add Data Store* dialog. 
   Type ‘input’ as the Data Store name and click **Ok**.

#. Repeat the above operation to create a Data Store called ‘output’.

#. Drag the Tool icon (|tool_icon|) from the toolbar and drop it into the 
   *Design View*. This will open the *Add Tool* dialog. Type ‘SpineOpt’ as 
   the Tool name and click **Ok**.

   .. note:: Each item in the *Design view* is equipped with three *connectors*
      (the small squares at the item boundaries).

#. Click on one of ‘input’ connectors and then on one of ‘SpineOpt’ connectors. 
   This will create a *connection* from the former to the latter.

#. Repeat the procedure to create a *connection* from `SpineOpt` to `output`. 
   It should look something like this:

   .. image:: img/case_study_a5_item_connections.png
      :align: center

#. From the main menu, select **File -> Save project**.


Configuring Julia
~~~~~~~~~~~~~~~~~

#. Go to Spine Toolbox main window and select **File -> Settings...**. This will 
   open the *Settings* dialog.

#. Go to the *Tools* page and select *Use Julia executable*.

#. Enter the path to your julia executable path or  leave blank to use the 
   executable in your PATH.

#. Choose your current project directory as the Julia project.

#. Also select *Use Python interpreter* and leave the path blank.

#. Click **Ok**.


Configuring SpineOpt 
~~~~~~~~~~~~~~~~~~~~

.. note:: This tutorial is written for SpineOpt 
   `version 0.4.0 <https://github.com/Spine-project/SpineOpt.jl/tree/v0.4.0>`_. 


#. Choose **File -> Tool configuration assistants... -> SpineOpt.jl** from the 
   main menu. The application will install the right version of SpineOpt.

#. Create a new file called `run_spineopt.jl` in your project directory
   and put the following contents to it:

   .. code-block:: julia

      using SpineOpt
      run_spineopt(ARGS...)

   Make sure that the activated package on line 2 equals the name of the directory
   you put SpineOpt source files.

#. Open the *Edit Tool Specification* form by clicking the wrench icon with
   a green plus sign and selecting **Create Tool Specification...**

   .. image:: img/create_tool_specification.png
         :align: center

   Type ‘SpineOpt’ as the name of the specification and select ‘Julia’ as the type.
   Unselect **Execute in work directory**. Select the previously created Julia 
   script as the main program file, and enter :code:`@@url_inputs@@ @@url_outputs@@` 
   to the command line arguments box. Hit **Ok** and save the specification as 
   `spineopt.json` in your project directory.

#. Now that you’ve created a specification you can link it to the Tool item. 
   Select `SpineOpt` item, and choose the ‘SpineOpt’ tool specification in the 
   *Tool Properties* panel. 

#. Save the project (**File -> Save project** or Ctrl+S).


Entering input data
===================

Creating input database
~~~~~~~~~~~~~~~~~~~~~~~

Before beginning, download `the SpineOpt database template
<https://raw.githubusercontent.com/Spine-project/SpineOpt.jl/v0.4.0/data/spineopt_template.json>`_.
Follow the steps below to create a new Spine database for SpineOpt in the 
`input` Data Store:

#. Select the `input` Data Store item in the *Design View*.

#. Go to *Data Store Properties* and hit **New Spine db**.

#. Still in *Data Store Properties*, click **Open editor**. This will open 
   the newly created database in the *Spine database editor*, looking similar to this:

   .. image:: img/case_study_a5_treeview_empty.png
      :align: center

   |

   .. note:: The *Spine database editor* is a dedicated interface within Spine Toolbox
      for visualizing and managing Spine databases.

#. Select **File -> Import...** and select the template file you previously downloaded. 
   You should then see classes like ‘commodity’, ‘connection’ and ‘model’ uder 
   the root node of the tree view panel on the left.

#. From the main menu, select **Session -> Commit** to open the *Commit changes* dialog.
   Enter ‘Import SpineOpt template’ as the message and click **Commit**.

Creating objects
~~~~~~~~~~~~~~~~

#. Follow the steps below to add power plants to the model as objects of class ``unit``:

   a. Go to *Object tree*,
      right-click on ``unit`` and select **Add objects** from the context menu. This will
      open the *Add objects* dialog.
   b. With your mouse, select the list of plant names from the text-box below
      and copy it to the clipboard (**Ctrl+C**):

      .. _pwr_plant_names:

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

   c. Go back to the *Add objects* dialog, select the first cell under the **object name** column
      and press **Ctrl+V**. This will paste the list of plant names from the clipboard into that column,
      looking similar to this:

        .. image:: img/add_power_plant_units.png
          :align: center

   d. Click **Ok**.
   e. Back in the *Spine database editor*, under *Object tree*, double click on ``unit``
      to confirm that the objects are effectively there.
   f. Commit changes with the message ‘Add power plants’.


#. Repeat the procedure to add discharge and spillway connections as objects of class ``connection``,
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

#. Repeat the procedure to add water nodes as objects of class ``node``, with the following names:

   .. _water_nodes_names:

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

#. Finally, add ``water`` and ``electricity`` as objects of class ``commodity``;
   ``electricity_node`` as an object of clas ``node``; ``electricity_load`` as 
   an object of class ``unit``; and ``some_week`` as object of class ``temporal_block``.


Specifying object parameter values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Still in the Database editor, choose object class ``model`` from the Object tree.
In *Object parameter value* view (in the middle of the window, usually), you can
edit and add new parameter values for the objects. Add a new parameter called 
``duration_unit`` with value ‘hour’ in to the table for the ``instance`` model object.
There are no other alternatives in this model, so choose ``Base``. 

Also add parameters ``model_start`` and ``model_end``. To enter a date value, 
right-click on the value field, select **Open in editor...** and choose 
``Datetime`` as the parameter type in the opened dialog. Enter values 
‘2020-01-01T00:00:00’ and ‘2019-01-08T00:00:00’, respectively. Finally, you should 
have all three parameters defined as in the figure below.

.. image:: img/case_study_a5_model_parameters.png
      :align: center

Following what you learned above, choose the object ``some_week`` of class 
``temporal_block`` and enter a new value for parameter ``resolution`` of type 
``Duration`` and with value ‘1h’. 

Enter parameter values for the ``node`` class objects according to the data below.
The values can be copied and pasted to the *Object parameter value* view.

.. literalinclude:: data/cs-a5-node-parameter-values.txt


Establishing relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tip:: To enter the same text on several cells, copy the text into the clipboard, then select all
   target cells and press **Ctrl+V**.


Follow the steps below to establish that power plant units receive water from 
the station's upper node, as relationships of class ``unit__from_node``:

   #. Go to *Relationship tree*,
      right-click on ``unit__from_node``
      and select **Add relationships** from the context menu. This will
      open the *Add relationships* dialog.
   #. Select again all `power plant names <pwr_plant_names_>`_ and copy them to the clipboard (**Ctrl+C**).
   #. Go back to the *Add relationships* dialog, select the first cell under the *unit* column
      and press **Ctrl+V**. This will paste the list of plant names from the clipboard into that column.
   #. Repeat the procedure to paste the list of *upper* `node names <water_nodes_names_>`_
      into the *node* column. 
   #. Check that the names of the power plants and the upper reservoirs match.
      Now the form should be looking like this:

      .. image:: img/add_pwr_plant_water_from_node.png
        :align: center

   #. Also connect unit ``electricity_load`` to node ``electricity_node``.
   #. Click **Ok**.
   #. Back in the *Spine database editor*, under *Relationship tree*, double click on
      ``unit__from_node`` to confirm that the relationships are effectively there.
   #. From the main menu, select **Session -> Commit** to open the *Commit changes* dialog.
      Enter ‘Add from nodes of power plants‘ as the commit message and click **Commit**.

Repeat the procedure to establish that power plant units release water to the 
station's lower node at each time slice in the one week horizon, as relationships 
of class ``unit__from_node``:

   .. image:: img/add_pwr_plant_water_to_node.png
      :align: center

Also establish a relationship so that the electricity load unit ``electricity_load``
takes electricity from the common electricity node ``electricity_node`` as 
a relationship of class ``unit__from_node``.

Repeat the above procedure to establish that power plant units generate electricity 
to the common electricity node at each time slice in the one week horizon, as 
relationships of class ``unit__to_node``:

   .. image:: img/add_pwr_plant_electricity_to_node.png
      :align: center

.. attention:: What do the ``unit__node__node`` relationships mean?

.. warning:: 

   **This is obsolete, right?**

   Repeat the procedure to establish that reservoir units take and release water 
   to and from the station's upper node at each time slice in the one week horizon,
   as relationships of class ``unit__node__direction__temporal_block``:

      .. image:: img/add_rsrv_water_to_from_node.png
         :align: center

   Repeat the procedure to establish the connection of each storage to the corresponding unit,
   as relationships of class ``storage__unit``:

   .. image:: img/add_storage_unit.png
      :align: center

   Repeat the procedure to establish that all storages store water,
   as relationships of class ``storage__commodity``:

   .. image:: img/add_storage_commodity.png
      :align: center



Establish relatiosnhips that discharge and spillway connections take water from 
the lower node of one station as relationships of class ``connection__from_node`` 
according to the following data (you can copy & paste into the 
**Add relationships** dialogue):

::

   Bastusel_to_Grytfors_disch	Bastusel_lower
   Bastusel_to_Grytfors_spill	Bastusel_upper
   Bergnäs_to_Slagnäs_disch	Bergnäs_lower
   Bergnäs_to_Slagnäs_spill	Bergnäs_upper
   Båtfors_to_Finnfors_disch	Båtfors_lower
   Båtfors_to_Finnfors_spill	Båtfors_upper
   Finnfors_to_Granfors_disch	Finnfors_lower
   Finnfors_to_Granfors_spill	Finnfors_upper
   Gallejaur_to_Vargfors_disch	Gallejaur_lower
   Gallejaur_to_Vargfors_spill	Gallejaur_upper
   Granfors_to_Krångfors_disch	Granfors_lower
   Granfors_to_Krångfors_spill	Granfors_upper
   Grytfors_to_Gallejaur_disch	Grytfors_lower
   Grytfors_to_Gallejaur_spill	Grytfors_upper
   Krångfors_to_Selsfors_disch	Krångfors_lower
   Krångfors_to_Selsfors_spill	Krångfors_upper
   Kvistforsen_to_downstream_disch	Kvistforsen_lower
   Kvistforsen_to_downstream_spill	Kvistforsen_upper
   Rebnis_to_Bergnäs_disch	Rebnis_lower
   Rebnis_to_Bergnäs_spill	Rebnis_upper
   Rengård_to_Båtfors_disch	Rengård_lower
   Rengård_to_Båtfors_spill	Rengård_upper
   Sadva_to_Bergnäs_disch	Sadva_lower
   Sadva_to_Bergnäs_spill	Sadva_upper
   Selsfors_to_Kvistforsen_disch	Selsfors_lower
   Selsfors_to_Kvistforsen_spill	Selsfors_upper
   Slagnäs_to_Bastusel_disch	Slagnäs_lower
   Slagnäs_to_Bastusel_spill	Slagnäs_upper
   Vargfors_to_Rengård_disch	Vargfors_lower
   Vargfors_to_Rengård_spill	Vargfors_upper

Complete the connections by adding relationships where the water is released to 
the upper node of the downstream station:

:: 

   Bastusel_to_Grytfors_disch	Grytfors_upper
   Bastusel_to_Grytfors_spill	Grytfors_upper
   Bergnäs_to_Slagnäs_disch	Slagnäs_upper
   Bergnäs_to_Slagnäs_spill	Slagnäs_upper
   Båtfors_to_Finnfors_disch	Finnfors_upper
   Båtfors_to_Finnfors_spill	Finnfors_upper
   Finnfors_to_Granfors_disch	Granfors_upper
   Finnfors_to_Granfors_spill	Granfors_upper
   Gallejaur_to_Vargfors_disch	Vargfors_upper
   Gallejaur_to_Vargfors_spill	Vargfors_upper
   Granfors_to_Krångfors_disch	Krångfors_upper
   Granfors_to_Krångfors_spill	Krångfors_upper
   Grytfors_to_Gallejaur_disch	Gallejaur_upper
   Grytfors_to_Gallejaur_spill	Gallejaur_upper
   Krångfors_to_Selsfors_disch	Selsfors_upper
   Krångfors_to_Selsfors_spill	Selsfors_upper
   Rebnis_to_Bergnäs_disch	Bergnäs_upper
   Rebnis_to_Bergnäs_spill	Bergnäs_upper
   Rengård_to_Båtfors_disch	Båtfors_upper
   Rengård_to_Båtfors_spill	Båtfors_upper
   Sadva_to_Bergnäs_disch	Bergnäs_upper
   Sadva_to_Bergnäs_spill	Bergnäs_upper
   Selsfors_to_Kvistforsen_disch	Kvistforsen_upper
   Selsfors_to_Kvistforsen_spill	Kvistforsen_upper
   Slagnäs_to_Bastusel_disch	Bastusel_upper
   Slagnäs_to_Bastusel_spill	Bastusel_upper
   Vargfors_to_Rengård_disch	Rengård_upper
   Vargfors_to_Rengård_spill	Rengård_upper


.. attention:: What do the ``connection__node__node`` relationships mean?

To establish that water nodes balance water and the electricity node balances 
electricity, create relationships between all upper and lower reservoir nodes 
and the ``water`` commodity as well as the ``electricity_node`` and ``electricity``.

   .. image:: img/add_node_commodity.png
      :align: center

Establish that all nodes are balanced at each time slice in the one week horizon
by creating relationships of class ``node__temporal_block`` for all the nodes 
and the temporal_block ``some_week``.

   .. image:: img/add_node_temporal_block.png
      :align: center


Specifying relationship parameter values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Relationships can also have parameters, and their values can be seen in the
*Relationship parameter value* panel. Following the procedure above for entering object parameter values,
add the following values for ``unit__from_node``:

.. literalinclude:: data/cs-a5-relationship-parameter-values.txt

Finally commit changes to the data store.


Executing the workflow
======================

Once the workflow is defined and input data is in place, the project is ready
to be executed. Hit the **Execute project** button (|execute_project|) on 
the toolbar.

You should see ‘Executing All Directed Acyclic Graphs’ printed to *Event log*
in the lower left panel (by default).
SpineOpt output messages will appear to the *Process Log* panel in the middle.
After some processing, ‘DAG 1/1 completed successfully’ appears and the 
execution is complete.


Examining the results
=====================

Select the output data store and open the database editor to it.

.. attention::

   What to do here?
