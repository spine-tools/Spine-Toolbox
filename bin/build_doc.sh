#!/bin/bash
#@TITLE Build Spine Toolbox docs

path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo Building Spine Toolbox documentation
pushd $path/../docs
make html
popd
