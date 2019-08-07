@ECHO OFF
@TITLE Build Spine Toolbox docs

ECHO Building Spine Toolbox documentation
sphinx-apidoc -f -o ..\docs\source\apidocs ..\spinetoolbox\ ..\spinetoolbox\setup.py
..\docs\make.bat html
