######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains tests for ZMQClient class.
:author: P. Savolainen (VTT)
:date:   15.6.2022
"""


import unittest
import json
import os
from unittest import mock
from tempfile import TemporaryDirectory
from pathlib import Path
from PySide2.QtWidgets import QApplication
from spinetoolbox.server.zmq_client import ZMQClient, ClientSecurityModel
from spine_engine.server.engine_server import EngineServer, ServerSecurityModel
from spine_items.tool.tool_specifications import PythonTool
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox, add_dc, add_tool


class TestZMQClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.toolbox = create_toolboxui_with_project(self._temp_dir.name)
        self.project = self.toolbox.project()
        self.host = "localhost"
        self.port = 5500
        self.service = EngineServer("tcp", self.port, ServerSecurityModel.NONE, "")

    def tearDown(self):
        self.service.close()
        self.project = None
        clean_up_toolbox(self.toolbox)
        self._temp_dir.cleanup()

    def test_zmq_client_execution(self):
        """Executes a DC->Tool DAG on a server remote server."""
        engine_data = self.make_engine_data_for_test_zipfile_project()
        msg_data_json = json.dumps(engine_data)
        zip_fname = "test_zipfile.zip"
        zip_fpath = os.path.join(str(Path(__file__).parent), zip_fname)
        client = ZMQClient("tcp", self.host, self.port, ClientSecurityModel.NONE, "")
        data_events = client.send(msg_data_json, zip_fpath, zip_fname)
        # for e in data_events:
        #     print(e)
        self.assertEqual("dag_exec_finished", data_events[-1][0])
        self.assertEqual("COMPLETED", data_events[-1][1])

    def make_engine_data_for_test_zipfile_project(self):
        """Returns an engine data dictionary for SpineEngine() for the project in file test_zipfile.zip.

        engine_data dict must be the same as what is passed to SpineEngineWorker() in
        spinetoolbox.project.create_engine_worker()
        """
        specification = PythonTool(name="helloworld2", tooltype="python", path="../../..",
                                   includes=["helloworld.py"], inputfiles=["input2.txt"],
                                   execute_in_work=True, settings=self.toolbox.qsettings(), logger=mock.Mock())
        self.toolbox.project().add_specification(specification, save_to_disk=False)
        add_tool(self.toolbox.project(), self.toolbox.item_factories, "helloworld", tool_spec="helloworld2")
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "Data Connection 1",
               file_refs=[{"type": "path", "relative": True, "path": "input2.txt"}])
        tool_item_dict = self.toolbox.project().get_item("helloworld").item_dict()
        dc_item_dict = self.toolbox.project().get_item("Data Connection 1").item_dict()
        spec_dict = specification.to_dict()
        spec_dict["definition_file_path"] = "./helloworld/.spinetoolbox/specifications/Tool/helloworld2.json"
        item_dicts = dict()
        item_dicts["helloworld"] = tool_item_dict
        item_dicts["Data Connection 1"] = dc_item_dict
        specification_dicts = dict()
        specification_dicts["Tool"] = [spec_dict]
        engine_data = {
            "items": item_dicts,
            "specifications": specification_dicts,
            "connections": [{"from": ["Data Connection 1", "left"], "to": ["helloworld", "right"]}],
            "jumps": [],
            "execution_permits": {"Data Connection 1": True, "helloworld": True},
            "items_module_name": "spine_items",
            "settings": {},
            "project_dir": "./helloworld",
        }
        return engine_data

    # @staticmethod
    # def test_connection_closing_loop(remoteIP, port):
    #     client = ZMQClient("tcp", remoteIP, int(port), ClientSecurityModel.NONE, "")
    #
    #     dict_data = test_ZMQClient._dict_data(
    #         items={
    #             'helloworld': {
    #                 'type': 'Tool',
    #                 'description': '',
    #                 'x': -91.6640625,
    #                 'y': -5.609375,
    #                 'specification': 'helloworld2',
    #                 'execute_in_work': False,
    #                 'cmd_line_args': [],
    #             },
    #             'Data Connection 1': {
    #                 'type': 'Data Connection',
    #                 'description': '',
    #                 'x': 62.7109375,
    #                 'y': 8.609375,
    #                 'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}],
    #             },
    #         },
    #         connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
    #         node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
    #         execution_permits={'Data Connection 1': True, 'helloworld': True},
    #         project_dir='./helloworld',
    #         specifications={
    #             'Tool': [
    #                 {
    #                     'name': 'helloworld2',
    #                     'tooltype': 'python',
    #                     'includes': ['helloworld.py'],
    #                     'description': '',
    #                     'inputfiles': ['input2.txt'],
    #                     'inputfiles_opt': [],
    #                     'outputfiles': [],
    #                     'cmdline_args': [],
    #                     'execute_in_work': True,
    #                     'includes_main_path': '../../..',
    #                     'definition_file_path': './helloworld/.spinetoolbox/specifications/Tool/helloworld2.json',
    #                 }
    #             ]
    #         },
    #         settings={
    #             'appSettings/previousProject': './helloworld',
    #             'appSettings/recentProjectStorages': './',
    #             'appSettings/recentProjects': 'helloworld<>./helloworld',
    #             'appSettings/showExitPrompt': '2',
    #             'appSettings/toolbarIconOrdering': 'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
    #             'appSettings/workDir': './Spine-Toolbox/work',
    #         },
    #         jumps=[],
    #         items_module_name='spine_items',
    #     )
    #     # print("test_connection_closing_loop(): sending request with data:")
    #     # print(dict_data)
    #     jsonTxt = json.dumps(dict_data)
    #     jsonTxt = json.dumps(jsonTxt)
    #     i = 0
    #     while i < 10:
    #         pathStr = str(os.path.realpath(Path(__file__).parent))
    #         print("test_connection_closing_loop(): sending file at path: %s" % pathStr)
    #         eventsData = client.send(jsonTxt, pathStr, "test_zipfile.zip")
    #         print("test_connection_closing_loop(): event data item count received: %d" % len(eventsData))
    #         # print(eventsData)
    #         if eventsData[len(eventsData) - 1][1] != "COMPLETED":
    #             return -1
    #         print("test msg %d sent/received, data size received: %d" % (i, len(eventsData)))
    #         i += 1
    #     client.close()
    #     return 0

    # @staticmethod
    # def test_invalid_file(remoteIP, port):
    #     client = ZMQClient("tcp", remoteIP, int(port), ClientSecurityModel.NONE, "")
    #     try:
    #         eventsData = client.send("dsds", "./dd", "test_zi.zip")
    #         return -1
    #     except Exception as e:
    #         print("print(Sending failed as expected due to invalid_file: %s" % e)
    #         return 0
    #
    # @staticmethod
    # def test_invalid_filename(remoteIP, port):
    #     client = ZMQClient("tcp", remoteIP, int(port), ClientSecurityModel.NONE, "")
    #     try:
    #         eventsData = client.send("dsds", "./dd", "")
    #         return -1
    #     except Exception as e:
    #         print("print(Sending failed as expected due to invalid_filename: %s" % e)
    #         return 0
    #
    # @staticmethod
    # def test_invalid_text(remoteIP, port):
    #     client = ZMQClient("tcp", remoteIP, int(port), ClientSecurityModel.NONE, "")
    #     try:
    #         pathStr = str(os.path.realpath(Path(__file__).parent))
    #         eventsData = client.send(None, pathStr, "test_zipfile.zip")
    #         return -1
    #     except Exception as e:
    #         print("print(Sending failed as expected due to invalid_text: %s" % e)
    #         return 0

    # @staticmethod
    # def test_invalid_remoteserverlocation():
    # read JSON file content, and parse it
    # f=open('msg_data1.txt')
    # msgData = f.read()
    # f.close()
    # msgDataJson=json.dumps(msgData)

    # try:
    #    eventsData=client.send(msgDataJson,"./","test_zipfile.zip")
    # except Exception as e:
    #    print("print(Sending failed as expected due to: %s"%e)


if __name__ == "__main__":
    unittest.main()
