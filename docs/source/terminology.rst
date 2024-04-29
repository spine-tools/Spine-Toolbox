.. Terminology section.
   Created: 31.8.2018

.. _Terminology:

***********
Terminology
***********

Here is a list of definitions related to Spine project, SpineOpt.jl, and Spine Toolbox.

- **Arc** Graph theory term. See *Connection*.
- **Case study** Spine project has 13 case studies that help to improve, validate and deploy
  different aspects of the SpineOpt.jl and Spine Toolbox.
- **Connection** (aka **Arrow**) an arrow on Spine Toolbox Design View that is used to connect project items
  to each other to form a DAG.
- **Data Connection** is a project item used to store a collection of data files that may or may not
  be in Spine data format. It facilitates data transfer from original data sources e.g. spreadsheet
  files to Spine Toolbox. The original data source file does not need to conform to the format that
  Spine Toolbox is capable of reading, since there we can use an interpreting layer (Importer) between
  the raw data and the Spine format database (Data Store).
- **Data Package** is a data container format consisting of a metadata descriptor file
  (``datapackage.json``) and resources such as data files.
- **Data sources** are all the original, unaltered, sources of data that are used to generate
  necessary input data for Spine Toolbox tools.
- **Data Store** is a project item. It's a Spine Toolbox internal data container which follows the
  Spine data model. A data store is implemented using a database, it may be, for example, an SQL
  database.
- **Design View** A *sub-window* on Spine Toolbox main window, where project items and connections
  are visualized.
- **Direct predecessor** Immediate predecessor. E.g. in DAG *x->y->z*, direct predecessor of node *z* is
  node *y*. See also predecessor.
- **Direct successor** Immediate successor. E.g. in DAG *x->y->z*, direct successor of node *x* is
  node *y*. See also successor.
- **Directed Acyclic Graph (DAG)** Finite directed graph with no directed cycles. It consists of
  vertices and edges. In Spine Toolbox, we use project items as vertices and connections as edges to
  build a DAG that represents a data processing chain (workflow).
- **Edge** Graph theory term. See *Connection*
- **Element** is what the entities making up a multi dimensional entity are called. See also multidimensional
  entity.
- **Importer** is a project item that can be used to import data from e.g. an Excel file, transform it
  to Spine data structure, and into a Data Store.
- **Loop** (aka **jump**) is a special sort of connection which only connects the two attached project
  items if the user defined loop condition is met.
- **Multidimensional entity/entity class** (aka N-D entity/class) An entity/entity class that consists of multiple
  other entities that are as it's members. Acts just like any other entity/entity class.
- **Node** Graph theory term. See *Project item*.
- **Predecessor** Graph theory term that is also used in Spine Toolbox. Preceding project
  items of a certain project item in a DAG. For example, in DAG *x->y->z*, nodes *x* and *y* are
  the predecessors of node *z*.
- **Project** in Spine Toolbox consists of project items and connections, which are used to build
  a data processing chain for solving a particular problem. Data processing chains are built and
  executed using the rules of Directed Acyclic Graphs. There can be any number of project items in a
  project.
- **Project item** Spine Toolbox projects consist of project items. Project items together with
  connections are used to build Directed Acyclic Graphs (DAG). Project items act as nodes and
  connections act as edges in the DAG. See :ref:`Project Items` for an up-to-date list on project
  items available in Spine Toolbox.
- **Scenario** A scenario is a meaningful data set for the target tool.
- **Spine data structure** Spine data structure defines the format for storing and moving data within
  Spine Toolbox. A generic data structure allows representation of many different modelling entities.
  Data structures have a class defining the type of entity they represent, can have properties and can
  be related to other data structures. Spine data structures can be manipulated and visualized within
  Spine Toolbox while SpineOpt.jl will be able to directly utilize as well as output them.
- **SpineOpt.jl** An interpreter, which formulates a solver-ready mixed-integer optimization
  problem based on the input data and the equations defined in the SpineOpt.jl. Outputs the solver
  results.
- **Source directory** In context of Tool specifications, a source directory is the directory where
  the main program file of the Tool specification is located. This is also the recommended place for
  saving the Tool specification file (.json).
- **Successor** Graph theory term that is also used in Spine Toolbox. Following project items of a
  certain project item in a DAG. For example, in DAG *x->y->z*, nodes *y* and *z* are the successors
  of node *x*.
- **Tool** is a project item that is used to execute Python, Julia, GAMS, executable scripts,
  or simulation models. This is done by creating a Tool specification defining the script
  or program the user wants to execute in Spine Toolbox. Then you need to attach the Tool specification
  to a Tool project item. Tools can be used to execute a computational process or a simulation model,
  or it can also be a process that converts data or calculates a new variable. In general, Tools may
  take some data as input and produce an output.
- **Tool specification** is a JSON structure that contains metadata required by Spine Toolbox to
  execute a computational process or a simulation model. The metadata contains; type of the program
  (Python, Julia, GAMS, executable), main program file (which can be e.g. a Windows batch (.bat) file
  or for Python scripts this would be the .py file where the __main__() method is located), All
  additional required program files, any optional input files (e.g. data), and output files. Also any
  command line arguments can be defined in a Tool specification. SpineOpt.jl is a Tool specification
  from Spine Toolbox's point-of-view.
- **Use case** Potential way to use Spine Toolbox. Use cases together are used to test the
  functionality and stability of Spine Toolbox and SpineOpt.jl under different potential circumstances.
- **Vertex** Graph theory term. See *Project item*.
- **View** A project item that can be used for visualizing project data.
- **Work directory** Tool specifications can be executed in *Source directory* or in *work directory*.
  When a Tool specification is executed in a work directory, Spine Toolbox creates a new *work*
  directory, copies all required and optional files needed for running the Tool specification to this
  directory and executes it there. After execution has finished, output or result files can be copied
  into a timestamped (archive) directory from the work directory.
