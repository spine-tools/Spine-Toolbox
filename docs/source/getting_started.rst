..  Tutorial for Spine Toolbox
    Created: 18.6.2018

.. |dc_icon| image:: ../../spinetoolbox/ui/resources/dc_icon.png
            :width: 24
.. |plus| image:: ../../spinetoolbox/ui/resources/plus.png
          :width: 16
.. |tool_icon| image:: ../../spinetoolbox/ui/resources/tool_icon.png
             :width: 24
.. |add_tool_template| image:: ../../spinetoolbox/ui/resources/add_tool.png
              :width: 24
.. |tool_template_options| image:: ../../spinetoolbox/ui/resources/tool_options.png
             :width: 24



.. _SpineData.jl: https://gitlab.vtt.fi/spine/data/tree/manuelma
.. _SpineModel.jl: https://gitlab.vtt.fi/spine/model/tree/manuelma
.. _Jupyter: http://jupyter.org/
.. _IJulia.jl: https://github.com/JuliaLang/IJulia.jl


***************
Getting Started
***************

Welcome to the Spine Toolbox's getting started guide.
In this guide you will learn two ways of running a `"Hello, World!" program
<https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`_ on Spine Toolbox.
The following topics are touched (although not exhaustively covered):

.. contents::
   :local:


Spine Toolbox Interface
-----------------------

The central element in Spine Toolbox's interface is the *Design View*,
where you can visualize and manipulate your project in a pictorial way.
Alongside *Design view* there are a few 'docked widgets' that provide additional functionality:

- *Project* provides a more concise view of your project, including:

   - *Items* currently in the project, grouped by category:
     Data Stores, Data Connections, Tools and Views.
   - *Tool templates* available in the project.

- *Properties* provides an interface to interact with the currently selected project item.
- *Event Log* shows relevant messages about every performed action.
- *Process Log* shows the output of executed Tools.
- *Julia console* provides an interface to interact with the Julia programming language,
  and also allows Spine Toolbox to execute Julia Tools.

.. tip:: You can drag-and-drop the Docked Widgets around the screen,
   customizing the interface at your will.
   Also, you can select which ones are shown/hidden using either the **View/Docked Widgets** menu,
   or the *Add Item* toolbar's context menu.
   Spine Toolbox will remember your configuration in between sessions.

.. tip:: Most elements in the Spine Toolbox's interface are equipped with *tool tips*. Leave your mouse
   cursor over an element (button, view, etc.) for a moment to make the tool tip appear.

Creating a Project
------------------

To create a new project, please do one of the following:

A) From the application main menu, select **File -> New...**
B) Press *Ctrl+N*.

The *New Project* form will show up.
Type 'hello world' in the name field ---we will leave the description empty this time--- and click **Ok**.

Congratulations, you have created a new project.

Creating a Tool template
------------------------

.. note:: Spine Toolbox is designed to run and connect multiple tools, which are specified using **Tool Templates**.
   You may think of a Tool Template as a self-contained program specification including a list of source files,
   required and optional input files, and expected output files. Once a Tool template is added to a project, it can
   then be associated to a **Tool** item for its execution as part of the project workflow.

In the *Project* widget, click on the 'add tool template button' (|add_tool_template|)
just below the *Tool templates* list, and select **New** from the popup menu.
The *Edit Tool Template* form will appear. Follow the instructions below to create a minimal Tool template:

- Type 'hello_world' in the *name* field.
- Select 'Executable' from the *type* dropdown list,
- Click on the plus button (|plus|) right next to the field that reads *Add main program file here...*, and
  select the option **Make new main program** from the popup menu.
- Now you should enter the name of the main program file for this tool template.
  If you are on Windows, enter 'hello_world.bat';
  if you are on Linux or Mac, enter 'hello_world.sh'. Click **Ok**.
- A new dialog will open where you can select a folder to save this main program file.
  Select any folder and click **Open**.

After all this, the *Edit Tool Template* form should be looking similar to this:

.. image:: img/hello_world_tool_template_editor.png
  :align: center

Click **Ok** at the bottom of the form. A new system dialog will appear, allowing you to
select a file name and location to save the Tool template we've just created.
Don't change the default file name, which should be 'hello_world.json'.
Just select a folder from your system (it can be the same where you saved the main program file)
and click **Save**.

Now you should see the new tool template in the *Project* widget, *Tool templates* list.

.. tip:: Saving the Tool template into a file allows you to add and use the same Tool template in
   another project. To do this, you just need to click on the add tool button (|add_tool_template|),
   select **Add existing...** from the popup menu, and then select the tool template file from your system.

Congratulations, you have just created your first minimal Tool template.

However, the main program file 'hello_world.bat' (or 'hello_world.sh') was created empty, so for the moment this Tool
template does absolutely nothing. To change that, we need to add instructions to that program file so it actually
does something when executed.

Right click on the 'hello_world' item in the *Tool templates* list and select **Edit main program file...** from the
context menu. This will open the file 'hello_world.bat' (or 'hello_world.sh') in your default text editor.

If you're on Windows and your main program file is called 'hello_world.bat',
enter the following into the file's content::

    @echo Hello, World!

If you're on Linux or Mac and your main program file is called 'hello_world.sh',
enter the following into the file's content::

    echo Hello, World!

Save the file.
Now, whenever 'hello_world.bat' (or 'hello_world.sh') is executed, the sentence 'Hello, World!'
will be printed to the standard output.


Adding a Tool item to the project
---------------------------------

.. note:: The **Tool** item is used to run Tool templates available in the project.

Let's add a Tool item to our project, so that we're able to run the Tool template we created above.
To add a Tool item please do one of the following:

A) From the application main menu, select **Edit -> Add Tool**.
B) Drag-and-drop the Tool icon (|tool_icon|) from the *Add Item* toolbar onto the *Design View*.

The *Add Tool* form will popup.
Type 'say hello world' in the name field, select 'hello_world' from the dropdown list just below, and click **Ok**.
Now you should see the newly added Tool item as an icon in the *Design View*,
and also as an entry in the *Project* widget, *Items* list, under the 'Tools' category. It should
look similar to this:

.. image:: img/say_hello_world_tool.png
   :align: center


Executing a Tool
----------------

As long as the 'say hello world' Tool item is selected, you will be able to see its *Properties* on the right part
of the window, looking similar to this:

.. image:: img/say_hello_world_tool_properties.png
   :align: center

Press **Execute**. This will execute the Tool template 'hello world',
which in turn will run the main program file 'hello_world.bat' (or 'hello_world.sh') in a dedicated process.

You can see more details about execution in the *Event log*. Once it's finished, you will see its output in
the *Process log*:

.. image:: img/hello_world_event_process_log.png
   :align: center

Congratulations, you just run your first Spine Toolbox project.

Editing a Tool template
-----------------------

To make things more interesting, we will now specify an *input file* for our 'hello_world' Tool template.

.. note:: Input files specified in the Tool template can be used by the program source files, to obtain some relevant
   information for the Tool's execution. When executed, a Tool item looks for input files in
   **Data Connection** and **Data Store** items connected to its input.

Click on the 'tool template options' button (|tool_template_options|) in 'say hello world'
*Properties*, and select **Edit Tool template** from the popup menu.
This will open the 'Edit Tool Template' form pre-filled with data from the 'hello_world' template.

Right below the *Input files* list, you will find two buttons. Click on the left one.
A dialog will appear so that you can enter a
name for a new input file. Type 'input.txt' and click **Ok**. The form
should now be looking like this:

.. image:: img/hello_world_input_tool_template_editor.png
  :align: center

Clik **Ok** at the bottom of the form.

So far so good. Now let's use this input file in our program.
Click on the 'tool template options' button (|tool_template_options|) again,
and this time select **Edit main program file...** from the popup menu. This will open the file
'hello_world.bat' (or 'hello_world.sh') in your default text editor.

If you're on Windows and your main program file is called 'hello_world.bat',
delete whatever it's in the file and enter the following instead::

    type input.txt

If you're on Linux or Mac and your main program file is called 'hello_world.sh',
delete whatever it's in the file and enter the following instead::

    cat input.txt

Save the file.
Now, whenever 'hello_world.bat' (or 'hello_world.sh') is executed, it will look for a file called 'input.txt'
in the current directory, and print its content to the standard output.

Press **Execute** in 'say hello world' *Properties* again.
*The execution will fail.* This is because the file 'input.txt' is not
made available for the Tool:

.. image:: img/hello_world_failed.png
  :align: center



Adding a Data Connection item to the project
--------------------------------------------

.. note:: The **Data Connection** item is used to hold and manipulate generic data files,
   so that other items, notably Tool items, can make use of that data.

Let's add a Data Connection item to our project, so that we're able to pass the file 'input.txt' to 'say hello world'.
To add a Data Connection item, please do one of the following:

A) From the application main menu, click **Edit -> Add Data Connection**.
B) Drag-and-drop the Data Connection icon (|dc_icon|) from the *Add Item* toolbar onto the *Design View*.

The *Add Data Connection* form will show up.
Type 'pass input txt' in the name field and click **Ok**.
Now you should see the newly added Data Connection item as an icon in the *Design View*,
and also as an entry in the *Project* widget, *Items* list, under the 'Data Connections' category. It should
look similar to this:

.. image:: img/pass_input_txt_dc_and_say_hello_world_tool.png
   :align: center


Adding data files to a Data Connection
--------------------------------------

As long as the 'pass input txt' Data Connection item is selected,
you will be able to see its *Properties* on the right part
of the window, looking similar to this:

.. image:: img/pass_input_txt_dc_properties.png
   :align: center

Right click anywhere within the *Data* box and select **New file...** from the context menu.
When prompted to enter a name for the new file, type 'input.txt' and click **Ok**.

Now you should see the newly created file in the *Data* list:

.. image:: img/pass_input_txt_dc_properties_with_file.png
   :align: center

Double click on this file to open it in your default text editor. Then enter the following into the file's content::

    Hello again, World!

Save the file.

Connecting project items
------------------------

As mentioned above, a Tool item looks for input files in
Data Connection and Data Store items connected to its input. Thus, what we need to do now is
create a *connection* from 'pass input txt' to 'say hello world', so the file 'input.txt' gets passed.

To do this, click on the *connector* button at the center of 'pass input txt' in the *Design view*, and then
on the corresponding button of 'say hello world'. This will create an arrow pointing from one to another,
as seen below:

.. image:: img/pass_input_txt_dc_to_say_hello_world_tool.png
   :align: center

Select 'say hello world' and press **Execute**. The Tool will run successfully this time:

.. image:: img/hello_again_world_event_process_log.png
   :align: center

That's all for now. I hope you've enjoyed following this guide as much as I enjoyed writing it. See you next time.
