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
A Zero-MQ client for exchanging messages between the toolbox and the remote server.
:author: P. Pääkkönen (VTT)
:date:   02.09.2021
"""


import sys
#sys.path.append('./../util')
import os
import zmq
import json
import time
import random

from spinetoolbox.server.util.ServerMessage import ServerMessage
from spinetoolbox.server.util.ServerMessageParser import ServerMessageParser
from spinetoolbox.server.util.EventDataConverter import EventDataConverter


class ZMQClient:


    def __init__(self,protocol,remoteHost,remotePort):
        """
        Args:
            protocol (string): Zero-MQ protocol
            remoteHost: location of the remote spine server
            remotePort(int): port of the remote spine server
        """
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        ret=self._socket.connect(protocol+"://"+remoteHost+":"+str(remotePort))
        #print("ZMQClient(): socket.connect() return value: %d"%ret)
        print("ZMQClient(): Connection established to %s:%d"%(remoteHost,remotePort))


    def send(self,text,fileLocation,fileName):
        """
        Args:
            text (string): 
            fileLocation (string): location of the binary file to be transferred
            fileName (string): name of the binary file to be transferred
        Returns:
            a list of tuples containing events+data
        """

        #check if folder and file exist
        print("ZMQClient.send(): path %s exists: %s file %s exists: %s."%(fileLocation,os.path.isdir(fileLocation),fileName,os.path.exists(fileLocation+fileName)))
        if os.path.isdir(fileLocation)==False or os.path.exists(fileLocation+fileName)==False:
            #print("ZMQClient.send(): invalid path or file.")
            raise ValueError("invalid path or file.")

        if text == None:
           raise ValueError("invalid input text")

        #Read file content
        f=open(fileLocation+fileName,'rb')
        fileData = f.read()
        f.close()

        #create message content
        randomId=random.randrange(10000000) 
        msg_parts=[]
        listFiles=[fileName]
        msg=ServerMessage("execute",str(randomId),text,listFiles)
        print("ZMQClient(): msg to be sent : %s"%msg.toJSON())
        part1Bytes = bytes(msg.toJSON(), 'utf-8')
        msg_parts.append(part1Bytes)
        msg_parts.append(fileData)

        #transfer
        self._socket.send_multipart(msg_parts)
        print("ZMQClient(): listening to a reply.")
        message = self._socket.recv()
 
        #decode
        msgStr=message.decode('utf-8')
        #print("ZMQClient()..Received reply %s" %msgStr)
        parsedMsg=ServerMessageParser.parse(msgStr)
        #get and decode events+data
        data=parsedMsg.getData()
        #print(type(data))
        jsonData=json.dumps(data)
        dataEvents=EventDataConverter.convertJSON(jsonData,True)
        return dataEvents


    def close(self):
        self._socket.close()
        print("ZMQClient(): Connection closed")



