.. Introduction page
   Created: 31.8.2018

************
Introduction
************

Terminology
===========
The following is a list of definitions that are used throughout the documentation and in Spine Toolbox.

Spine project Terminology
-------------------------
- **Case study** Spine project has 13 case studies that help to improve, validate and deploy
  different aspects of the Spine Model and Spine Toolbox.
- **Data Interface** is a component in Spine Toolbox, which handles connecting to and importing
  from external data sources.
- **Data Package** is a data container format consisting of a metadata descriptor file
  (‘datapackage.json’) and resources such as data files.
- **Data sources** are all the original, unaltered, sources of data that are used to generate
  necessary input data for Spine Toolbox tools.
- **Scenario** A scenario combines data connections to form a meaningful data set for the target tool.
- **Spine data structure** Spine data structure defines the format for storing and moving data within
  Spine Toolbox. A generic data structure allows representation of many
  different modelling entities. Data structures have a class defining the type of
  entity they represent, can have properties and can be related to other data
  structures. Spine data structures can be manipulated and visualized within
  Spine Toolbox while Spine Model will be able to directly utilize as well as
  output them.
- **Spine Model** An interpreter, which formulates a solver-ready mixed-integer optimization
  problem based on the input data and the equations defined in the Spine
  Model. Outputs the solver results.
- **Use case** Potential way to use Spine Toolbox. Use cases together are used to test the
  functionality and stability of Spine Toolbox and Spine Model under different
  potential circumstances.

Spine Toolbox Terminology
-------------------------
- **Spine Toolbox Project** is a Toolbox concept and consists of a data processing chain that
  is built by the user for solving a particular problem. Current items that constitute a project are;
  Data Connection, Data Store, Tool, and View. There can be any number of these items in a project, and
  they can be connected by drawing links between them.
- **Data Connection** is a project item, which facilitates data transfer from original data sources,
  e.g. spreadsheet files or databases, to Spine Toolbox. The original data source file does not need to
  conform to the format that Spine Toolbox is capable of reading, since there is an interpreting layer
  between them (Data Interface).
- **Data Store** is a Spine Toolbox internal data container which follows the Spine data
  model. A data store is implemented using a database, it may be, for example, an SQL database.
- **Tool** can be a computation process or a simulation model, or it can also be a script to
  convert data or calculate a new variable. Tool takes some data as input and produces an output.
  Tool contains a reference to the model code, external program that executes the code, and input
  data that the model code requires. Spine Model is a Tool from Spine Toolbox's point-of-view.
- **View** A project item that can be used for visualizing project data.
