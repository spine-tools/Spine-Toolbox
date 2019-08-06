#!/bin/bash
#@TITLE Build Spine Toolbox docs

echo Building Spine Toolbox documentation
sphinx-apidoc -f -o ../docs/source/ ../spinetoolbox/ ../spinetoolbox/setup.py
pushd ../docs
make html
popd
