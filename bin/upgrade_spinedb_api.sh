#!/bin/bash
#@TITLE Upgrading spinedb_api

printf '\n'
echo "This is a script for upgrading spinedb_api.
Copyright (C) <2017-2018>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
under certain conditions; See files COPYING and COPYING.LESSER for details."
printf '\n'

echo "USAGE:
'bash upgrade_spinedb_api.sh'            upgrade from master branch
'bash upgrade_spinedb_api.sh dev'        upgrade from dev branch"
printf '\n'


if [ $# -eq 0 ] # no arguments passed
then
  printf '\n'
  echo "Upgrading from 'master' branch"
  printf '\n'
  pip3 install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@master
elif [ $1 = "dev" ]
then
  printf '\n'
  echo "Upgrading from 'dev' branch"
  printf '\n'
  pip3 install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git@dev
else
  printf '\n'
  echo "Unknown argument $1. Please see USAGE."
  printf '\n'
fi
