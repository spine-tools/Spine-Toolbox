######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains facilities to open and execute projects without GUI.

:authors: A. Soininen (VTT)
:date:   29.4.2020
"""
from .dag_handler import DirectedGraphHandler


def open_project(project_dict):
    project_items = list()
    dag_handler = DirectedGraphHandler()
    for catecory_name, item_dicts in project_dict["objects"].items():
        for item_name, item_dict in item_dicts.items():
            dag_handler.add_dag_node(item_name)

    for connection in project_dict["project"]["connections"]:
        from_name = connection["from"][0]
        to_name = connection["to"][0]
        dag_handler.add_graph_edge(from_name, to_name)
    return project_items, dag_handler
