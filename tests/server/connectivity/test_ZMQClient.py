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
A tester for ZMQClient 
:author: P. Pääkkönen (VTT)
:date:   02.09.2021
"""


import sys
import zmq
import json

sys.path.append('./../../../spinetoolbox/server/connectivity')
sys.path.append('./../../../spinetoolbox/server/util')
from ZMQClient import ZMQClient



class test_ZMQClient:

    @staticmethod
    def _dict_data(
        items, connections, node_successors,
          execution_permits,specifications,settings,
          project_dir
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
        Returns:
            dict
        """
        item = dict()
        item['items']=items
        item['connections']=connections
        item['node_successors']=node_successors
        item['execution_permits']=execution_permits
        item['specifications']=specifications
        item['settings']=settings
        item['project_dir']=project_dir
        return item



    @staticmethod
    def test_connection_closing_loop():
        client=ZMQClient("tcp","193.166.160.216",5555)

        #read JSON file content, and parse it
        #f=open('msg_data1.txt')
        #msgData = f.read()
        #f.close()
        #msgDataJson=json.loads(msgData)
        #msgDataJson=msgData
        #print("test_ZMQClient(): converted JSON (type: %s): %s"%(type(msgDataJson),msgDataJson))

        dict_data = test_ZMQClient._dict_data(items={'helloworld': {'type': 'Tool', 'description': '', 'x': -91.6640625,
            'y': -5.609375, 'specification': 'helloworld2', 'execute_in_work': True, 'cmd_line_args': []},
            'Data Connection 1': {'type': 'Data Connection', 'description': '', 'x': 62.7109375, 'y': 8.609375,
             'references': [{'type': 'path', 'relative': True, 'path': 'input2.txt'}]}},
            connections=[{'from': ['Data Connection 1', 'left'], 'to': ['helloworld', 'right']}],
            node_successors={'Data Connection 1': ['helloworld'], 'helloworld': []},
            execution_permits={'Data Connection 1': True, 'helloworld': True},
            project_dir = '/home/ubuntu/sw/spine/helloworld',
            specifications = {'Tool': [{'name': 'helloworld2', 'tooltype': 'python',
            'includes': ['helloworld.py'], 'description': '', 'inputfiles': ['input2.txt'],
            'inputfiles_opt': [], 'outputfiles': [], 'cmdline_args': [], 'execute_in_work': True,
            'includes_main_path': '../../..',
            'definition_file_path':
            '/home/ubuntu/sw/spine/helloworld/.spinetoolbox/specifications/Tool/helloworld2.json'}]},
            settings = {'appSettings/previousProject': '/home/ubuntu/sw/spine/helloworld',
            'appSettings/recentProjectStorages': '/home/ubuntu/sw/spine',
            'appSettings/recentProjects': 'helloworld<>/home/ubuntu/sw/spine/helloworld',
            'appSettings/showExitPrompt': '2',
            'appSettings/toolbarIconOrdering':
            'Importer;;View;;Tool;;Data Connection;;Data Transformer;;Gimlet;;Exporter;;Data Store',
            'appSettings/workDir': '/home/ubuntu/sw/spine/Spine-Toolbox/work'})
        print("test_connection_closing_loop(): sending request with data:")
        print(dict_data)
        jsonTxt=json.dumps(dict_data)
        jsonTxt=json.dumps(jsonTxt)
        i=0
        while i <10:
            eventsData=client.send(jsonTxt,"./","test_zipfile.zip")
            print("test_connection_closing_loop(): event data item count received: %d"%len(eventsData))
            print(eventsData)
            if len(eventsData)!=30:
                return -1
            print("test msg %d sent/received, data size received: %d"%(i,len(eventsData)))
            i+=1
        client.close()
        return 0


    @staticmethod
    def test_invalid_file():
        client=ZMQClient("tcp","193.166.160.216",5555)
        try:
            eventsData=client.send("dsds","./dd","test_zi.zip")
            return -1
        except Exception as e:
            print("print(Sending failed as expected due to invalid_file: %s"%e)
            return 0


    @staticmethod
    def test_invalid_filename():
        client=ZMQClient("tcp","193.166.160.216",5555)
        try:
            eventsData=client.send("dsds","./dd","")
            return -1
        except Exception as e:
            print("print(Sending failed as expected due to invalid_filename: %s"%e)
            return 0


    @staticmethod
    def test_invalid_text():
        client=ZMQClient("tcp","193.166.160.216",5555)
        try:
            eventsData=client.send(None,"./","test_zipfile.zip")
            return -1
        except Exception as e:
            print("print(Sending failed as expected due to invalid_text: %s"%e)
            return 0


    #@staticmethod
    #def test_invalid_remoteserverlocation():
        #read JSON file content, and parse it
        #f=open('msg_data1.txt')
        #msgData = f.read()
        #f.close()
        #msgDataJson=json.dumps(msgData)

        #client=ZMQClient("tcp","193.166.160.217",5557)
        #try:
        #    eventsData=client.send(msgDataJson,"./","test_zipfile.zip")
        #except Exception as e:
        #    print("print(Sending failed as expected due to: %s"%e)




#run tests
ret1=test_ZMQClient.test_invalid_file()
ret2=test_ZMQClient.test_invalid_text()
ret3=test_ZMQClient.test_invalid_filename()
#test_ZMQClient.test_invalid_remoteserverlocation()
ret4=test_ZMQClient.test_connection_closing_loop()

if ret1==-1 or ret2==-1 or ret3==-1 or ret4==-1:
    print("tests failed")
else:
    print("tests OK")



