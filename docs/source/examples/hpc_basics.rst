.. _HPC Basics:

====================================================
Background on High-Performance Cluster (HPC) Systems
====================================================

This section describes briefly how common HPC systems work. It is designed to be general and portable,
so it applies to:

- University HPC clusters
- Company internal clusters
- Cloud HPC environments (AWS, Azure)

If you are already familiar with HPC systems, you can jump directly to the next section :ref:`Spine Toolbox on HPC`.

*********************
How HPC Clusters Work
*********************

Most HPC systems share the same architecture:

- Login node: where you connect and prepare jobs
- Compute nodes: where jobs run
- Scheduler (Slurm): assigns resources and executes jobs

.. warning::

   Do not run heavy computations on the login node.

.. figure:: ../img/tutorials/hpc_workflow.png
   :width: 100%
   :align: center

   Overview of the HPC workflow for running an energy optimization model.
   The user prepares and submits a job from a local machine, which is scheduled
   and executed on compute nodes. Results are then retrieved back to the local environment.

Explain:
- Flow goes from local machine → scheduler → compute nodes → results
- Emphasizes separation between submission and execution

.. figure:: ../img/tutorials/hpc_architecture.png
   :width: 100%
   :align: center

   Conceptual structure of an HPC cluster, showing login nodes,
   scheduler, and compute nodes. Users interact only with the login node,
   while computational workloads are executed on compute nodes.

Explain:
- User interacts with login node
- Scheduler dispatches jobs
- Compute nodes run jobs in parallel

.. figure:: ../img/tutorials/job_lifecycle.png
   :width: 100%
   :align: center

   Lifecycle of a Slurm job, including submission, queuing, execution,
   and completion stages.

Explain:

States:
- PENDING
- RUNNING
- COMPLETED

Helps users understand why jobs wait

Prerequisites
-------------

Required Access
^^^^^^^^^^^^^^^

- SSH access:

  .. code-block:: bash

     ssh username@cluster.address

- Project allocation (if required)


Required Software
^^^^^^^^^^^^^^^^^

- Python (3.10+)
- Spine Toolbox v0.10.8+
- Pyomo
- Solver (Gurobi, CPLEX, CBC, GLPK)


Connecting to the Cluster
-------------------------

Login
^^^^^

.. code-block:: bash

   ssh username@cluster.address


File Transfer
^^^^^^^^^^^^^

.. code-block:: bash

   scp -r my_project/ username@cluster:/home/username/

or:

.. code-block:: bash

   rsync -avz my_project/ username@cluster:/home/username/my_project/


Understanding the Cluster Environment
-------------------------------------

Common Directories
^^^^^^^^^^^^^^^^^^

- ``$HOME``: persistent storage
- ``$SCRATCH``: fast temporary storage


Module System
^^^^^^^^^^^^^

.. code-block:: bash

   module avail
   module load python
   module load gurobi
   module list


Preparing Your Pyomo Model
--------------------------

Example Structure
^^^^^^^^^^^^^^^^^

::

   my_project/
   ├── model.py
   ├── data/
   │   └── input.csv
   ├── requirements.txt
   └── run_model.py


Minimal Pyomo Example
^^^^^^^^^^^^^^^^^^^^^

``model.py``:

.. code-block:: python

   from pyomo.environ import *

   def create_model():
       model = ConcreteModel()

       model.x = Var(domain=NonNegativeReals)
       model.y = Var(domain=NonNegativeReals)

       model.obj = Objective(expr=2*model.x + 3*model.y, sense=maximize)

       model.constraint = Constraint(expr=model.x + model.y <= 10)

       return model


Solver Script
^^^^^^^^^^^^^

``run_model.py``:

.. code-block:: python

   from pyomo.environ import *
   from model import create_model

   model = create_model()

   solver = SolverFactory("gurobi")

   result = solver.solve(model, tee=True)

   model.display()

   with open("results.txt", "w") as f:
       f.write(str(result))


Setting Up Python Environment
-----------------------------

Virtual Environment
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate
   pip install pyomo


Conda (optional)
^^^^^^^^^^^^^^^^

.. code-block:: bash

   conda create -n energy_model python=3.10 pyomo
   conda activate energy_model


Writing a Slurm Job Script
--------------------------

Create ``job.sh``:

.. code-block:: bash

   #!/bin/bash
   #SBATCH --job-name=energy_model
   #SBATCH --output=output.log
   #SBATCH --error=error.log
   #SBATCH --time=02:00:00
   #SBATCH --cpus-per-task=4
   #SBATCH --mem=8G

   module load python
   module load gurobi

   source venv/bin/activate

   python run_model.py


Key Parameters
^^^^^^^^^^^^^^

- ``--job-name``: Job name
- ``--time``: Maximum runtime
- ``--cpus-per-task``: CPU cores
- ``--mem``: Memory
- ``--output``: Output file
- ``--error``: Error file


Submitting the Job
------------------

.. code-block:: bash

   sbatch job.sh


Monitoring the Job
------------------

Check queue:

.. code-block:: bash

   squeue -u username

Job details:

.. code-block:: bash

   scontrol show job JOBID

View logs:

.. code-block:: bash

   tail -f output.log


Debugging Common Issues
-----------------------

Job Stuck in Queue
^^^^^^^^^^^^^^^^^^

- Cluster is full
- Resource request too large

Memory Errors
^^^^^^^^^^^^^

Increase memory:

.. code-block:: bash

   #SBATCH --mem=16G


Solver Not Found
^^^^^^^^^^^^^^^^

.. code-block:: bash

   module load gurobi

Check installation:

.. code-block:: bash

   which gurobi_cl


Python Module Missing
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install pyomo


Parallelization Strategies
--------------------------

Multi-threaded Solver
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   solver.options["Threads"] = 4

Match with:

.. code-block:: bash

   #SBATCH --cpus-per-task=4


Scenario Parallelization
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   #SBATCH --array=1-50

Python:

.. code-block:: python

   import os
   scenario = int(os.getenv("SLURM_ARRAY_TASK_ID"))


Running Large Energy Models
---------------------------

Input Data
^^^^^^^^^^

- Use efficient formats
- Avoid unnecessary I/O

Output Handling
^^^^^^^^^^^^^^^

Organize outputs:

::

   results/scenario_1/
   results/scenario_2/


Scratch Usage
^^^^^^^^^^^^^

.. code-block:: bash

   cd $SCRATCH


Retrieving Results
------------------

.. code-block:: bash

   scp username@cluster:/home/user/results/ ./results/

or:

.. code-block:: bash

   rsync -avz username@cluster:/results/ ./results/


Best Practices
--------------

Always:

- Test locally first
- Run small cases
- Use version control
- Log outputs

Avoid:

- Running on login node
- Over-requesting resources
- Excessive file writing


Reproducibility
---------------

Requirements file:

::

   pyomo
   pandas
   numpy


Containers (Advanced)
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   apptainer run my_container.sif


Example Workflow Summary
------------------------

1. Develop model locally
2. Upload files

   .. code-block:: bash

      scp -r my_project cluster:~

3. Connect

   .. code-block:: bash

      ssh cluster

4. Load modules

   .. code-block:: bash

      module load python gurobi

5. Submit job

   .. code-block:: bash

      sbatch job.sh

6. Monitor

   .. code-block:: bash

      squeue

7. Retrieve results

   .. code-block:: bash

      scp cluster:results/* .
