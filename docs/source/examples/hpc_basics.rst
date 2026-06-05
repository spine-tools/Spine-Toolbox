.. _HPC Basics:

====================================================
Background on High-Performance Cluster (HPC) Systems
====================================================

This section briefly describes how common HPC systems work. The description is intentionally general so it applies to:

- University HPC clusters
- Company internal clusters
- Cloud-based HPC environments (e.g., AWS, Azure)

If you are already familiar with HPC systems, you can jump directly to the next section :ref:`Spine Toolbox on HPC`.

************
Introduction
************

Most HPC systems follow a similar architecture composed of three main components:

- **Login node**: the entry point to the system where users connect, prepare job scripts, and submit jobs
- **Compute nodes**: the machines where the actual computational work is executed
- **Scheduler (e.g., Slurm)**: the system responsible for allocating resources and dispatching jobs to compute nodes

.. figure:: ../img/tutorials/hpc_architecture.png
   :width: 100%
   :align: center

   Conceptual structure of an HPC cluster

Users typically interact only with the login node. After a job is submitted, the scheduler assigns it to available compute nodes, where it runs—often in parallel across multiple CPUs or nodes.

.. warning::

   Do not run heavy computations on the login node. It is intended only for job preparation and submission.

*****************
Workflow Overview
*****************

A typical HPC workflow separates job preparation from execution:

1. The user prepares input data and job scripts on their local machine
2. The job is submitted to the scheduler via the login node
3. The scheduler places the job in a queue and assigns resources when available
4. The job runs on compute nodes
5. Results are stored on the cluster and can be retrieved back to the local environment

This separation allows HPC systems to efficiently share resources among many users.

.. figure:: ../img/tutorials/hpc_workflow.png
   :width: 100%
   :align: center

   Overview of the HPC workflow for running an energy optimization model.
   The user prepares and submits a job from a local machine, which is scheduled
   and executed on compute nodes. Results are then retrieved back to the local environment.

*************
Job Lifecycle
*************

When a job is submitted to the scheduler (such as Slurm), it goes through several states:

- **PENDING**: the job is waiting in the queue for resources to become available
- **RUNNING**: the job is actively executing on compute nodes
- **COMPLETED**: the job has finished successfully (or terminated with an error)

Understanding these states helps explain why jobs may not start immediately—waiting in the queue is normal and depends on factors such as resource availability and system load.

.. figure:: ../img/tutorials/job_lifecycle.png
   :width: 100%
   :align: center

   Lifecycle of a Slurm job, including submission, queuing, execution,
   and completion stages.


*************************
Connecting to the Cluster
*************************

Login
-----


.. code-block:: bash

   ssh username@cluster.address


File Transfer
-------------

.. code-block:: bash

   scp -r my_project/ username@cluster:/home/username/

or:

.. code-block:: bash

   rsync -avz my_project/ username@cluster:/home/username/my_project/

*************************************
Understanding the Cluster Environment
*************************************

Common Directories
------------------

- ``$HOME``: persistent storage
- ``$SCRATCH``: fast temporary storage


Module System
-------------

.. code-block:: bash

   module avail
   module list

**************************
Writing a Slurm Job Script
**************************

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
--------------

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

***********************
Debugging Common Issues
***********************

Job Stuck in Queue
------------------

- Cluster is full
- Resource request too large

Memory Errors
-------------

Increase memory:

.. code-block:: bash

   #SBATCH --mem=16G


Solver Not Found
----------------

.. code-block:: bash

   module load gurobi

Check installation:

.. code-block:: bash

   which gurobi_cl


Python Module Missing
---------------------

.. code-block:: bash

   pip install pyomo


**************
Best Practices
**************

Always:

- Test locally first
- Run small cases
- Use version control
- Log outputs

Avoid:

- Running on login node
- Over-requesting resources
- Excessive file writing
