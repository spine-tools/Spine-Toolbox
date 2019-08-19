#!/bin/bash
#@TITLE Build Spine Toolbox docs

echo Building Spine Toolbox documentation
pushd ../docs
make html
popd
