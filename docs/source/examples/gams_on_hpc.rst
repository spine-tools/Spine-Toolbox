.. _Spine Toolbox on HPC:

=======================================
Running Spine Toolbox projects on HPC's
=======================================

.. contents::
   :depth: 1
   :local:

************
Introduction
************

This tutorial demonstrates how to run Spine Toolbox project involving `GAMS <https://www.gams.com/>`_
workflows on a High-Performance Computing (HPC) system using the SLURM scheduler.

The guide assumes you have access to a Linux-based HPC cluster with a shared filesystem and SLURM
installed. You also need a valid GAMS license and basic familiarity with the Linux command line.

You will learn the full workflow:

::

   Local machine → Cluster login → Upload files → Submit job → Monitor → Retrieve results

****************************************************
HPC's with container support (apptainer/singularity)
****************************************************

The easiest way to run Spine Toolbox projects involving GAMS is to use *apptainer* containers. Log in to the Login
node of your HPC and check if *apptainer* is available in your HPC with the following command:

.. code-block:: bash

    apptainer --version

If this fails, try checking if *apptainer* is available as a module:

.. code-block:: bash

    module avail apptainer

If the response is a version number or a list of package names and version numbers, you are good to continue to the
next section. If you see an error message or something like 'module not available', skip the next section and
continue from (`HPC's without container support`_).

.. Note::

    If the previous commands failed, you can still try if `singularity` is available with `singularity --version` or
    `module avail singularity`. Apptainer was previously called singularity.

About Apptainer
---------------

Apptainer is an open source container platform designed to be simple, fast, and secure.
There are other container platforms as well, but Apptainer is designed for ease-of-use on shared
systems and in high performance computing (HPC) environments. The container is a single file (.sif),
which you can build yourself from a .def file or you can download a ready-to-go container
from **<gams.sif>**.

Building the Apptainer Container
--------------------------------

If you want to build the container yourself, please use Linux or Windows Subsystem for Linux (WSL) on Windows.
Building Apptainer containers is done using *.def* files. You can `view and copy gams.def on your own system
here <../_static/gams.def>`_. Install Go and apptainer and build **gams.sif** with the following command:

.. code-block:: bash

   apptainer build --fakeroot gams.sif gams.def

Why --fakeroot? See https://apptainer.org/docs/user/latest/fakeroot.html#fakeroot-feature

When the build process has completed, you can use the `shell` command to spawn a new shell within your
container and interact with it as though it were a virtual machine.

.. code-block:: bash

    apptainer shell gams.sif

For example, you can check the versions of Python and Gams with `python --version` and `gams ?` respectively
inside the shell.

Running a Spine Toolbox project on an HPC
-----------------------------------------

Prerequisites:
- Access rights to an HPC
- Apptainer/Singularity as a system package or as a module
- License file for Gams
- Spine Toolbox project with a Gams Tool
- Container file (downloaded `gams.sif` or another .sif file)
- PuTTY and WinSCP on Windows (optional but recommended)

1. Download gams.sif
2. Upload gams.sif to HPC, e.g. to path /jobs/<usename>/sifs/gams.sif
3. Upload Spine Toolbox project to HPC, e.g. to path /jobs/<username>/projects/<project_name>
4. Upload GAMS license to HPC, e.g. to path /jobs/<username>/gamslicense
5. Upload Slurm script `run_on_hpc.sh` to Spine Toolbox project folder, e.g.
    to /jobs/<username>/projects/<project_name>

**run_on_hpc.sh**

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=spinetoolbox_on_hpc
    #SBATCH --output=out.txt
    #SBATCH --error=err.txt
    #SBATCH --time=00:30:00
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=4G

    apptainer exec /jobs/ttepsa/sifs/gams.sif spinetoolbox --execute-only $PWD/


.. attention::

    Line endings in Slurm scripts such as `run_on_hpc.sh` must be Unix style (LF).

.. note::
    If your HPC offers *apptainer* as a module, you must add `module load apptainer` to the Slurm script before the
    `exec` command.

**Key parameters**
    - ``--job-name``: Job name
    - ``--time``: Maximum runtime
    - ``--cpus-per-task``: CPU cores
    - ``--mem``: Memory
    - ``--output``: Output file
    - ``--error``: Error file

6. Edit the Slurm script by adding the license

    The example project works fine with the demo license but for real use cases you need a Gams license.

7. Submit job to Slurm Scheduler

.. code-block:: bash

    sbatch run_on_hpc.sh

The response will be something like

```
Submitted batch job 1303767
```

where 1303767 is the job id

8. Check status of submitted job

.. code-block:: bash

    squeue -j <job_id>

where *<job_id>* is the id returned by the `sbatch` command.
To check the status of all of your submitted tasks, run

.. code-block:: bash

    squeue -u $USER

If this command fails, replace $USER with your user name. When a job disappears from the the list returned by
the `squeue` command, it is finished.

9. Check job output files

Since `out.txt` and `err.txt` were given in the Slurm script as the values for *--output* and *--error*, you
can find the stdout and stderr of your job in these files. The file `err.txt` is empty if everything is Ok.
To view the files:

.. code-block:: bash

    cat out.txt
    cat err.txt

10. Final job status

.. code-block:: bash

    sacct -j <job_id>

where *<job_id>* is the id returned by the `sbatch` command.
This command returns something like:

    ```
    JobID           JobName  Partition    Account  AllocCPUS      State ExitCode
    ------------ ---------- ---------- ---------- ---------- ---------- --------
    1303767      spinetool+        all     ba6401          1  COMPLETED      0:0
    1303767.bat+      batch                ba6401          1  COMPLETED      0:0
    1303767.ext+     extern                ba6401          1  COMPLETED      0:0
    ```

11. Live monitoring

.. code-block:: bash

    watch -n 2 squeue -u $USER

Another option is to use `tail`:

.. code-block:: bash

   tail -f out.txt

Again, if $USER is not defined, replace it with your user name. This function tails the job progress and updates
every two seconds.

12. Checking the results

The result files and output from executing the project will be inside the project item folders just like
when executing the project in Spine Toolbox locally. One way to view the results, is to download
the project folder back into your local computer, start Spine Toolbox, and open the project there.

*******************************
HPC's without container support
*******************************

If apptainer is not available in your HPC system, there's a little bit more setup involved.

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

Job Stuck in Queue
++++++++++++++++++

- Cluster is full
- Resource request too large

Memory Errors
+++++++++++++

Increase memory:

.. code-block:: bash

   #SBATCH --mem=16G


Solver Not Found
++++++++++++++++

.. code-block:: bash

   module load gurobi

Check installation:

.. code-block:: bash

   which gurobi_cl


Python Module Missing
+++++++++++++++++++++

.. code-block:: bash

   pip install pyomo

Module Not Found
++++++++++++++++

- Check available modules:

.. code-block:: bash

   module avail

- Contact HPC support if GAMS is not provided

**************************
Performance Considerations
**************************

- Use job arrays for parallel workloads
- Avoid running many serial jobs in one script
- Request appropriate memory and runtime

Large-scale workflows are typically parallelized across scenarios rather than within a single GAMS run.
