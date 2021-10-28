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
Tester for Remote Spine Engine Manager. 
:authors: P. Pääkkönen (VTT)
:date:   06.09.2021
"""

import sys
import time
import os
import shutil
from zipfile import ZipFile
from pathlib import Path

# sys.path.append('./../..')
# sys.path.append('./../../spinetoolbox')
# sys.path.append('./../../spinetoolbox/server')
# sys.path.append('./../../spinetoolbox/server/connectivity')
# sys.path.append('./../../spinetoolbox/server/util')

# from LocalSpineEngineManager import LocalSpineEngineManager
from spinetoolbox.spine_engine_worker import SpineEngineWorker
from spinetoolbox.spine_engine_manager import RemoteSpineEngineManager2


class test_RemoteSpineEngineManager:
    @staticmethod
    def _dict_data(
        items,
        connections,
        node_successors,
        execution_permits,
        specifications,
        settings,
        project_dir,
        jumps,
        items_module_name,
    ):
        """Returns a dict to be passed to the class.
        Args:
            items (list(dict)): See SpineEngine.__init()
            connections (list of dict): See SpineEngine.__init()
            node_successors (dict(str,list(str))): See SpineEngine.__init()
            execution_permits (dict(str,bool)): See SpineEngine.__init()
            specifications (dict(str,list(dict))): SpineEngine.__init()
            settings (dict): SpineEngine.__init()
            project_dir (str): SpineEngine.__init()
            jumps (List of jump dicts): SpineEngine.__init()
            items_module_name (str): SpineEngine.__init()

        Returns:
            dict
        """
        item = dict()
        item['items'] = items
        item['connections'] = connections
        item['jumps'] = jumps
        item['node_successors'] = node_successors
        item['execution_permits'] = execution_permits
        item['items_module_name'] = items_module_name
        item['specifications'] = specifications
        item['settings'] = settings
        item['project_dir'] = project_dir
        return item

    @staticmethod
    def run_DAG(protocol, host, port):
        testSuccess = -1
        connDict = {}
        connDict["appSettings/remoteHost"] = host
        connDict["appSettings/remotePort"] = port
        connDict["appSettings/remoteSecurityModel"] = ""
        # print("run_DAG() using dict as input for connecting: ")
        # print(connDict)
        manager = RemoteSpineEngineManager2(connDict)
        # prepare data
        dict_data = test_RemoteSpineEngineManager._dict_data(
            items={
                'helloworld': {
                    'type': 'Tool',
                    'description': '',
                    'x': -91.6640625,
                    'y': -5.609375,
                    'specification': 'helloworld2',
                    'execute_in_work': False,
                    'cmd_line_args': [],
                },
                'Data Connection 1': {
                    'type': 'Data Connection',
                    'description': '',
                    'x': 62.7109375,
                    'y': 8.609375,
                    'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}],
                },
            },
            connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
            node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
            execution_permits={'Data Connection 1': True, 'helloworld': True},
            project_dir='./helloworld',
            specifications={
                'Tool': [
                    {
                        'name': 'helloworld2',
                        'tooltype': 'python',
                        'includes': ['helloworld.py'],
                        'description': '',
                        'inputfiles': ['input2.txt'],
                        'inputfiles_opt': [],
                        'outputfiles': [],
                        'cmdline_args': [],
                        'execute_in_work': True,
                        'includes_main_path': '../../..',
                        'definition_file_path': './helloworld/.spinetoolbox/specifications/Tool/helloworld2.json',
                    }
                ]
            },
            settings={
                'appSettings/previousProject': './helloworld',
                'appSettings/recentProjectStorages': './',
                'appSettings/recentProjects': 'helloworld<>./helloworld',
                'appSettings/showExitPrompt': '2',
                'appSettings/toolbarIconOrdering': 'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
                'appSettings/workDir': './Spine-Toolbox/work',
            },
            jumps=[],
            items_module_name='spine_items',
        )
        # print("run_DAG(): sending request with data:")
        # print(dict_data)
        manager.run_engine(dict_data)
        while True:
            event, data = manager.get_engine_event()
            if event != None and data != None:
                # print("event type: %s, data type: %s"%(type(event),type(data)))
                # print("Received event: %s"%event)
                # print("Received data: %s"%data)
                if event == 'dag_exec_finished' and data == 'COMPLETED':
                    testSuccess = 0
                    break
            else:
                time.sleep(0.1)
        time.sleep(1)
        manager.stop_engine()
        return testSuccess

    # @staticmethod
    # def run_DAG_empty_response(protocol,host,port):
    #    manager=RemoteSpineEngineManager2(protocol,host,port)
    # prepare data
    #    dict_data = test_RemoteSpineEngineManager._dict_data(items={'helloworld': {'type': 'Tool', 'description': '', 'x': -91.6640625,
    #        'y': -5.609375, 'specification': 'helloworld2', 'execute_in_work': True, 'cmd_line_args': []},
    #        'Data Connection 1': {'type': 'Data Connection', 'description': '', 'x': 62.7109375, 'y': 8.609375,
    #         'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}]}},
    #        connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
    #        node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
    #        execution_permits={'Data Connection 1': True, 'helloworld': True},
    #        project_dir = '/home/ubuntu/sw/spine/helloworld',
    #        specifications = {'Tool': [{'name': 'helloworld2', 'tooltype': 'python',
    #        'includes_main_path': '../../..',
    #        'definition_file_path':
    #        '/home/ubuntu/sw/spine/helloworld/.spinetoolbox/specifications/Tool/helloworld2.json'}]},
    #        settings = {'appSettings/previousProject': '/home/ubuntu/sw/spine/helloworld',
    #        'appSettings/recentProjectStorages': '/home/ubuntu/sw/spine',
    #        'appSettings/recentProjects': 'helloworld<>/home/ubuntu/sw/spine/helloworld',
    #        'appSettings/showExitPrompt': '2',
    #        'appSettings/toolbarIconOrdering':
    #        'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
    #        'appSettings/workDir': '/home/ubuntu/sw/spine/Spine-Toolbox/work'})
    #    print("run_DAG(): sending request with data:")
    #    print(dict_data)
    #    manager.run_engine(dict_data)
    #    while True:
    #        event,data=manager.get_engine_event()
    #        if event!=None and data!=None:
    #            #print("event type: %s, data type: %s"%(type(event),type(data)))
    #            print("Received event: %s"%event)
    #            print("Received data: %s"%data)
    #            if event=='dag_exec_finished':
    #                break
    #        else:
    #            time.sleep(0.1)
    #    manager.stop_engine()

    @staticmethod
    def run_DAG_noreading(protocol, host, port):
        testSuccess = -1
        connDict = {}
        connDict["appSettings/remoteHost"] = host
        connDict["appSettings/remotePort"] = port
        connDict["appSettings/remoteSecurityModel"] = ""
        manager = RemoteSpineEngineManager2(connDict)
        # prepare data
        dict_data = test_RemoteSpineEngineManager._dict_data(
            items={
                'helloworld': {
                    'type': 'Tool',
                    'description': '',
                    'x': -91.6640625,
                    'y': -5.609375,
                    'specification': 'helloworld2',
                    'execute_in_work': False,
                    'cmd_line_args': [],
                },
                'Data Connection 1': {
                    'type': 'Data Connection',
                    'description': '',
                    'x': 62.7109375,
                    'y': 8.609375,
                    'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}],
                },
            },
            connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
            node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
            execution_permits={'Data Connection 1': True, 'helloworld': True},
            project_dir='./helloworld',
            specifications={
                'Tool': [
                    {
                        'name': 'helloworld2',
                        'tooltype': 'python',
                        'includes': ['helloworld.py'],
                        'description': '',
                        'inputfiles': ['input2.txt'],
                        'inputfiles_opt': [],
                        'outputfiles': [],
                        'cmdline_args': [],
                        'execute_in_work': True,
                        'includes_main_path': '../../..',
                        'definition_file_path': './helloworld/.spinetoolbox/specifications/Tool/helloworld2.json',
                    }
                ]
            },
            settings={
                'appSettings/previousProject': './helloworld',
                'appSettings/recentProjectStorages': './',
                'appSettings/recentProjects': 'helloworld<>./helloworld',
                'appSettings/showExitPrompt': '2',
                'appSettings/toolbarIconOrdering': 'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
                'appSettings/workDir': './Spine-Toolbox/work',
            },
            jumps=[],
            items_module_name='spine_items',
        )

        # print("run_DAG(): sending request with data:")
        # print(dict_data)
        ret1 = manager.run_engine(dict_data)
        try:
            ret2 = manager.run_engine(dict_data)
        except:
            #        if ret1==0 and ret2==-1:
            print("run_DAG_noreading() exception as expected due to multiple requests, when already running a DAG")
            testSuccess = 0
        manager.stop_engine()
        return testSuccess

    @staticmethod
    def run_DAG_loop(protocol, host, port):
        testSuccess = -1
        connDict = {}
        connDict["appSettings/remoteHost"] = host
        connDict["appSettings/remotePort"] = port
        connDict["appSettings/remoteSecurityModel"] = ""

        # manager=RemoteSpineEngineManager2(connDict)
        # prepare data
        dict_data = test_RemoteSpineEngineManager._dict_data(
            items={
                'helloworld': {
                    'type': 'Tool',
                    'description': '',
                    'x': -91.6640625,
                    'y': -5.609375,
                    'specification': 'helloworld2',
                    'execute_in_work': True,
                    'cmd_line_args': [],
                },
                'Data Connection 1': {
                    'type': 'Data Connection',
                    'description': '',
                    'x': 62.7109375,
                    'y': 8.609375,
                    'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}],
                },
            },
            connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
            node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
            execution_permits={'Data Connection 1': True, 'helloworld': True},
            project_dir='./helloworld',
            specifications={
                'Tool': [
                    {
                        'name': 'helloworld2',
                        'tooltype': 'python',
                        'includes': ['helloworld.py'],
                        'description': '',
                        'inputfiles': ['input2.txt'],
                        'inputfiles_opt': [],
                        'outputfiles': [],
                        'cmdline_args': [],
                        'execute_in_work': True,
                        'includes_main_path': '../../..',
                        'definition_file_path': './helloworld/.spinetoolbox/specifications/Tool/helloworld2.json',
                    }
                ]
            },
            settings={
                'appSettings/previousProject': './helloworld',
                'appSettings/recentProjectStorages': './',
                'appSettings/recentProjects': 'helloworld<>./helloworld',
                'appSettings/showExitPrompt': '2',
                'appSettings/toolbarIconOrdering': 'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
                'appSettings/workDir': './Spine-Toolbox/work',
            },
            jumps=[],
            items_module_name='spine_items',
        )
        # print("run_DAG(): sending request with data:")
        # print(dict_data)
        for x in range(0, 3):
            manager = RemoteSpineEngineManager2(connDict)
            manager.run_engine(dict_data)
            while True:
                event, data = manager.get_engine_event()
                if event != None and data != None:
                    # print("event type: %s, data type: %s"%(type(event),type(data)))
                    # print("Received event: %s"%event)
                    # print("Received data: %s"%data)
                    if event == 'dag_exec_finished' and data == 'COMPLETED':
                        if x == 2:
                            testSuccess = 0
                        break
                else:
                    time.sleep(0.1)
            time.sleep(1)
            manager.stop_engine()
        return testSuccess

    @staticmethod
    def invalid_config():
        try:
            manager = RemoteSpineEngineManager2(None, "", 3433)
        except:
            print("exception raised as expected due to invalid input data")
            return 0

    @staticmethod
    def invalid_config2():
        try:
            manager = RemoteSpineEngineManager2("", "193.166.160.216", "", 3433)
        except:
            print("exception raised as expected due to invalid input data")
            return 0

    @staticmethod
    def initialise_test_folder(zipFile, destFolder):
        pathStr = os.path.join(str(Path(__file__).parent), destFolder)
        folderExists = os.path.isdir(pathStr)
        if folderExists == False:
            os.mkdir(pathStr)
        with ZipFile(zipFile, 'r') as zipObj:
            print("initialise_test_folder() extracting ZIP-file to folder: %s" % pathStr)
            zipObj.extractall(pathStr)
            zipObj.close()

    @staticmethod
    def delete_test_folder(folder):
        pathStr = os.path.join(str(Path(__file__).parent), folder)
        shutil.rmtree(pathStr)
        print("removed test folder: %s" % pathStr)


if __name__ == '__main__':

    args = sys.argv[1:]
    print("test_RemoteSpineEngineManager(): arguments:%s" % args)

    if len(args) < 2:
        print("provide remote spine_server IP address and port")

    else:
        test_RemoteSpineEngineManager.initialise_test_folder("test_zipfile.zip", "helloworld")
        # run tests
        test1 = test_RemoteSpineEngineManager.invalid_config()
        test2 = test_RemoteSpineEngineManager.invalid_config2()
        test3 = test_RemoteSpineEngineManager.run_DAG_noreading("tcp", args[0], int(args[1]))
        # test_RemoteSpineEngineManager.run_DAG_empty_response("tcp","193.166.160.216",5555)
        time.sleep(1)
        test4 = test_RemoteSpineEngineManager.run_DAG("tcp", args[0], int(args[1]))

        test5 = test_RemoteSpineEngineManager.run_DAG_loop("tcp", args[0], int(args[1]))
        test_RemoteSpineEngineManager.delete_test_folder("helloworld")

        if test1 == 0 and test2 == 0 and test3 == 0 and test4 == 0 and test5 == 0:
            print("tests OK")

        else:
            print("tests failed")
