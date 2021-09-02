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
    def test_connection_closing_loop():
        client=ZMQClient("tcp","193.166.160.216",5555)

        #read JSON file content, and parse it
        f=open('msg_data1.txt')
        msgData = f.read()
        f.close()
        msgDataJson=json.dumps(msgData)
        
        i=0
        while i <10:
            eventsData=client.send(msgDataJson,"./","test_zipfile.zip")
            #print(eventsData)
            print("test msg %d sent/received"%i)
            i+=1
        client.close()


    @staticmethod
    def test_invalid_file():
        client=ZMQClient("tcp","193.166.160.216",5555)
        try:
            eventsData=client.send(msgDataJson,"./dd","test_zi.zip")
        except Exception as e:
            print("print(Sending failed as expected due to: %s"%e)

#run tests
test_ZMQClient.test_invalid_file()
test_ZMQClient.test_connection_closing_loop()



