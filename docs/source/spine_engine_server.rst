.. Spine Engine Server
   Created 31.10.2022

.. |play-all| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
   :width: 16

.. _Spine Engine Server:

*******************
Spine Engine Server
*******************

Notes
-----
Here is a list of items that you should be aware of when running projects on Spine Engine Server.

- **Projects must be self-contained**. The project directory must contain all input and output
  files, file/db references, Specification files and scripts.
- **Work or Source directory execution mode** setting is ignored. Tools are always executed in 'source'
  directory, i.e. in the directory where the Tool Spec main script resides.
- **Python Basic Console**. Interpreter setting in Tool Specification Editor is ignored. Basic Console runs the
  same Python that was used in starting the Server.
- **Python Jupyter Console**. Kernel spec setting in Tool Specification Editor is ignored. Jupyter Console is
  launched using the **python3** kernel spec. This must be installed before the server is started. See instructions
  below.
- **Julia Basic Console**. Julia executable setting in Tool Specification Editor is ignored. Basic
  Console runs the Julia that is found in the server machine's PATH. See installation instructions below.
- **Julia Jupyter Console**. Kernel spec setting in Tool Specification Editor is ignored. Jupyter
  Console is launched using the **julia-1.8** kernel spec. This must be installed before the server is started.
  See instructions below.

Setting up Spine Engine Server
------------------------------
You can either install the entire Spine Toolbox or just the required parts to run the Spine Engine Server.

Minimal Installation
********************
Spine Engine server does not need the entire Spine Toolbox installation. Only *spine-engine*, *spinedb-api*
and *spine-items*. Note that the dependencies of *spine-items* are not needed. Here are the step-by-step
instructions for a minimal installation:

1.1 Make a miniconda environment & activate it

1.2. Clone `spine-engine <https://github.com/spine-tools/spine-engine>`_

1.3. cd to *spine-engine* repo root, run::

   pip install -e .

1.4. Clone `spine-items <https://github.com/spine-tools/spine-items>`_

1.5. cd to *spine-items* repo root

1.6. Install *spine-items* **without dependencies** by running::

   pip install --no-deps -e .


Full Installation
*****************
Install Spine Toolbox regularly

1.1. Make a miniconda environment & activate

1.2. Clone `Spine Toolbox <https://github.com/spine-tools/Spine-Toolbox>`_

1.3. Follow the `installation instructions in README.md <https://github.com/spine-tools/Spine-Toolbox#installation>`_

Finalize Setting Up and Start Server
************************************

2. Create security credentials (optional)

   - cd to `<spine_engine_repo_root>/spine_engine/server/`
   - Create security certificates by running::

      python certificate_creator.py

   - The certificates are created into `<spine_engine_repo_root>/spine_engine/server/certs/` directory.
   - Configure allowed endpoints by creating file
     `<spine_engine_repo_root>/spine_engine/server/connectivity/certs/allowEndpoints.txt`
   - Add IP addresses of the remote end points to the file

3. Install IPython kernel spec (*python3*) to enable Jupyter Console execution of Python Tools

   - Run::

      python -m pip install ipykernel

4. Install Julia 1.8

   - Download from https://julialang.org/downloads/ or run `apt-get install julia` on Ubuntu

5. Install IJulia kernel spec (*julia-1.8*) to enable Jupyter Console execution of Julia tools

   - Open Julia REPL and press `]` to enter pkg mode. Run::

         add IJulia

   - This installs `julia-1.8` kernel spec to `~/.local/share/jupyter/kernels` on Ubuntu or to
     `%APPDATA%\jupyter\kernels` on Windows

6. Start Spine Engine Server

   - cd to `<spine_engine_repo_root>/spine_engine/server/`
   - Without security, run::

      python start_server.py 50001

   - where 50001 is the server port number.
   - With Stonehouse security, run::

      python start_server.py 50001 StoneHouse ./certs

   - where 50001 is an example server port number, StoneHouse is the security model, and the path is the folder
     containing the security credentials.

.. Note:: Valid port range is 49152-65535.

Setting up Spine Toolbox (client)
---------------------------------
1. (Optional) If server is started using StoneHouse security, copy security credentials from the server to
   some directory. Server's secret key does not need to be copied.

2. Start Spine Toolbox and open a project

3. Open the **Engine** page in Spine Toolbox Settings (**File -> Settings...**)

   - Enable remote execution from the checkbox (Enabled)
   - Set up the Spine Engine Server settings (host, port, security model, and security folder).
     Host is 127.0.0.1 when the Server runs on the same computer as the client
   - Click Ok, to close and save the new Settings

4. Click |play-all| to execute the project
