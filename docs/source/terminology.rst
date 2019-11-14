.. Introduction page. Only has the terminology for now.
   Created: 31.8.2018

.. _Terminology:

***********
Terminology
***********

Here is a list of definitions that are used throughout the User Guide and in Spine Toolbox.

Spine Toolbox Terminology
-------------------------
- **Data Connection** is a project item used to store a collection of data files that may or may not be in
  Spine data format. It facilitates data transfer from original data sources e.g. spreadsheet files to Spine
  Toolbox. The original data source file does not need to conform to the format that Spine Toolbox is capable
  of reading, since there we can use an interpreting layer (Importer) between the raw data and the Spine
  format database (Data Store).
- **Data Store** is a project item. It's a Spine Toolbox internal data container which follows the Spine data
  model. A data store is implemented using a database, it may be, for example, an SQL database.
- **Exporter** is a project item that allows exporting a Spine data structure from a Data Store into a file
  which can be used as an input file in a Tool.
- **Importer** is a project item that can be used to import data from e.g. an Excel file, transform it
  to Spine data structure, and into a Data Store.
- **Project** is a Spine Toolbox concept and consists of a data processing chain that
  is built by the user for solving a particular problem. Current items that constitute a project are;
  Data Connection, Data Store, Tool, View, Importer and Exporter. There can be any number of these items in a
  project, and they can be connected by drawing links between them.
- **Source directory** When in context of Tool specifications, a Source directory is the directory where the main
  program file of the Tool specification is located. This is also the recommended place where the Tool specification
  file (.json) is saved.
- **Tool** is a project item that is used to execute Tool specifications. To execute a script or a simulation
  model in Spine Toolbox, you attach a Tool specification to a Tool.
- **Tool specification** can be a computational process or a simulation model, or it can also be a script to
  convert data or calculate a new variable. Tool specification takes some data as input and produces an output.
  Tool specification contains a reference to the model code, external program that executes the code, and input
  data that the model code requires. Spine Model is a Tool specification from Spine Toolbox's point-of-view.
- **View** A project item that can be used for visualizing project data.
- **Work directory** A directory where Tool specification execution takes place. When a Tool is executed, Spine Toolbox
  creates a new *work* directory, copies all required and optional files needed for running the Tool specification
  to this directory and executes it there. After execution has finished, output or result files can be archived
  into a timestamped results directory from the work directory.


Spine project Terminology
-------------------------
- **Case study** Spine project has 13 case studies that help to improve, validate and deploy
  different aspects of the Spine Model and Spine Toolbox.
- **Importer** is a component in Spine Toolbox, which handles connecting to and importing
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
