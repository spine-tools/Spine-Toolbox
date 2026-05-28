.. _GAMS on HPC:


Running GAMS Workflows on HPC with SLURM
========================================

.. contents::
   :depth: 1
   :local:

Introduction
------------

This tutorial demonstrates how to run workflows involving `GAMS <https://www.gams.com/>`_
models on a High-Performance Computing (HPC) system using the SLURM scheduler.
It covers both single-job execution and scalable workflows such as parameter sweeps.

The guide assumes a Linux-based HPC cluster with a shared filesystem and SLURM installed.

Prerequisites
-------------

Before starting, ensure the following:

- Access to an HPC system with SLURM
- A working installation of GAMS (module or user-installed)
- A valid GAMS license accessible on compute nodes
- Basic familiarity with the Linux command line

Verify GAMS installation:

.. code-block:: bash

   gams ?

If GAMS is installed correctly, this command prints version and usage information.


Accessing GAMS on HPC
---------------------

Option 1: Using a Module
++++++++++++++++++++++++

Many HPC systems provide GAMS via environment modules:

.. code-block:: bash

   module avail gams
   module load gams

Verify:

.. code-block:: bash

   which gams


Option 2: User Installation
+++++++++++++++++++++++++++

If GAMS is not provided:

1. Download the Linux version from the GAMS website
2. Extract it in your home or project directory
3. Add it to your PATH:

.. code-block:: bash

   export PATH=$HOME/gams:$PATH

Ensure that your license file is accessible (e.g., ``gamslice.txt``).


Directory Layout
----------------

A clean workflow structure is recommended:

.. code-block:: text

   project/
   ├── model.gms
   ├── data/
   │   └── input.csv
   ├── scripts/
   │   └── run.sh
   ├── results/
   └── logs/


Running a Single GAMS Job
-------------------------

Create a SLURM batch script:

.. code-block:: bash

   #!/bin/bash
   #SBATCH --job-name=gams_job
   #SBATCH --output=logs/job_%j.out
   #SBATCH --error=logs/job_%j.err
   #SBATCH --time=01:00:00
   #SBATCH --mem=4G

   module load gams  # or set PATH manually

   cd $SLURM_SUBMIT_DIR

   gams model.gms lo=2

Submit the job:

.. code-block:: bash

   sbatch scripts/run.sh

Output files (e.g., ``.lst``, ``.gdx``) will be generated in the working directory.


Passing Parameters to GAMS
--------------------------

GAMS supports command-line parameters:

.. code-block:: bash

   gams model.gms --scenario=1

In your GAMS model:

.. code-block:: xml

   $if not set scenario $set scenario 1
   scalar scenario / %scenario% /;

You can pass parameters from SLURM scripts or workflows.


Running Parameter Sweeps with SLURM Arrays
------------------------------------------

For multiple scenarios, use SLURM job arrays:

.. code-block:: bash

   #!/bin/bash
   #SBATCH --job-name=gams_array
   #SBATCH --array=1-10
   #SBATCH --output=logs/job_%A_%a.out
   #SBATCH --time=01:00:00
   #SBATCH --mem=4G

   module load gams

   SCENARIO=$SLURM_ARRAY_TASK_ID

   gams model.gms --scenario=$SCENARIO lo=2

Submit:

.. code-block:: bash

   sbatch scripts/run_array.sh

This creates 10 parallel jobs with different input parameters.


Using Input Data Files
----------------------

GAMS can read external data (e.g., CSV):

.. code-block:: xml

   $call csv2gdx data/input.csv output=data.gdx id=mydata

   $gdxin data.gdx
   $load mydata

Ensure input paths are relative to the working directory or use absolute paths.


Managing Output
---------------

It is good practice to organize outputs:

- Redirect logs using SLURM directives
- Move results into dedicated directories

Example:

.. code-block:: bash

   mkdir -p results/$SCENARIO
   gams model.gms --scenario=$SCENARIO o=results/$SCENARIO/output.lst

Common Issues and Troubleshooting
---------------------------------

License Errors
++++++++++++++

- Ensure license file is accessible on compute nodes
- Check environment variables if needed:

.. code-block:: bash

   export GAMSLICE=/path/to/gamslice.txt

File Not Found
++++++++++++++

- Verify paths are correct relative to the SLURM working directory
- Use:

.. code-block:: bash

   echo $PWD

Module Not Found
++++++++++++++++

- Check available modules:

.. code-block:: bash

   module avail

- Contact HPC support if GAMS is not provided

Performance Considerations
--------------------------

- Use job arrays for parallel workloads
- Avoid running many serial jobs in one script
- Request appropriate memory and runtime

Large-scale workflows are typically parallelized across scenarios rather than within a single GAMS run.


Advanced Topics
---------------

Containers (Optional)
+++++++++++++++++++++

If supported, you can use Apptainer/Singularity:

.. code-block:: bash

   apptainer exec gams.sif gams model.gms

This improves reproducibility across systems.

Workflow Automation
+++++++++++++++++++

You can integrate GAMS into larger workflows using tools such as:

- Snakemake
- Nextflow
- Makefiles

These tools help manage dependencies and automate multi-step pipelines.
