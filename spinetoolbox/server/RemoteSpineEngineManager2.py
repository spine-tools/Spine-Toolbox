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
Contains a Remote Spine Engine Manager. This class is responsible to remote DAG execution.
:authors: P. Pääkkönen (VTT)
:date:   03.09.2021
"""

import sys
import threading
import time
import json
import ast
#sys.path.append('..')
#sys.path.append('./connectivity')
sys.path.append('./util')
from enum import Enum

#from spinetoolbox.server.util.ServerMessage import ServerMessage
from spinetoolbox.server.connectivity.ZMQClient import ZMQClient
from spinetoolbox.spine_engine_manager import SpineEngineManagerBase
from spinetoolbox.server.util.FilePackager import FilePackager

#states of this class 
class RemoteSpineEngineManagerState2(Enum):
    IDLE = 1 #no requests pending and events+data of an earlier request has been extracted with get_event()
    RUNNING = 2  #request is being processed with the remote server 
    REPLY_RECEIVED = 3 # a reply has been received fromn the remote server
    CLOSED = 4 # the manager has been closed

    def __str__(self):
        return str(self.name)


class RemoteSpineEngineManager2(SpineEngineManagerBase,threading.Thread):


    #ZIP-file name to be used
    ZipFileName="project_package"

    """
    Initialiser.
    Args:
        protocol(string):Zero-MQ protocol 
        remoteHost(string): host name/IP address of the remote spine_engine
        remotePort(string): port of the remote spine_engine
    """
    def __init__(self,protocol,remoteHost,remotePort):

        if protocol==None or remoteHost==None or remotePort==None:
            raise ValueError("invalid input values to RemoteSpineEngineManager2.")

        if len(protocol)==0 or len(remoteHost)==0:
            raise ValueError("invalid input values (protocol,remoteHost) to RemoteSpineEngineManager2.")

        threading.Thread.__init__(self)
        print("RemoteSpineEngineManager()")
        self.zmqClient=ZMQClient(protocol,remoteHost,remotePort)
        self._state=RemoteSpineEngineManagerState2.IDLE
        self._requestPending=False
        self._inputData=None
        self._outputData=None
        self._outputDataIteratorIndex=0
        self.start()


    def run_engine(self, engine_data):
        """Runs an engine with given data.

        Args:
            engine_data (dict): The engine data.
        """

        if self._state==RemoteSpineEngineManagerState2.IDLE and self._requestPending==False:
            self._inputData=engine_data
            self._requestPending=True
            print("RemoteSpineEngineManager2.run_engine(): Pending request execution..")
            return 0

        else:
            print("RemoteSpineEngineManager2.run_engine(): Cannot execute due to pending request or state: %s"%str(self._state))
            return -1


    def get_engine_event(self):
        """Gets next event from engine currently running.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        """
        if self._state==RemoteSpineEngineManagerState2.REPLY_RECEIVED:
            eventData=self._outputData[self._outputDataIteratorIndex]
            self._outputDataIteratorIndex+=1

            if self._outputDataIteratorIndex==len(self._outputData):
                print("get_engine_event() all events+data has been received, returning to IDLE")
                self._state=RemoteSpineEngineManagerState2.IDLE 

            try:
                #print("get_engine_event() transforming data: %s"%eventData[1])
                dataDict=ast.literal_eval(eventData[1])
                #dataDict=json.loads(eventData[1])
                #print(type(dataDict))
                #print("get_engine_event() returning: event: %s, data: %s"%(eventData[0],dataDict))
                return (eventData[0],dataDict)
            except:   #these exceptions are needed due to some dict-strings being returned without quotes
                      # and status code (not a dict string) see: SpineEngine._process_event()
                if eventData[1].find('{')==-1:
                    #print("get_engine_event() Failure in parsing, returning a status code.")
                    return (eventData[0],eventData[1])
                quotedData=self._addQuotesToDictString(eventData[1])
                #print("get_engine_event() Failure in parsing, modified quotes to str: %s"%quotedData)
                dataDict=ast.literal_eval(quotedData)
                #print("get_engine_event() returning: event: %s, data: %s"%(eventData[0],dataDict))
                return (eventData[0],dataDict)

        else:
            print("get_engine_event(): returning empty tuple, reply has not been received yet.")
            return (None,None)


    def stop_engine(self):
        """Stops engine currently running."""
        self._state=RemoteSpineEngineManagerState2.CLOSED
        print("RemoteSpineEngineManager2.stop_engine()")


    def run(self):
        print("RemoteSpineEngineManager2.run()")

        while(self._state!=RemoteSpineEngineManagerState2.CLOSED):
            #run request 
            if self._requestPending==True and self._state==RemoteSpineEngineManagerState2.IDLE:
                #change state
                print("RemoteSpineEngineManager2.run() Started running..")
                self._state==RemoteSpineEngineManagerState2.RUNNING

                #transform dict to JSON string
                jsonTxt=json.dumps(self._inputData)
                print("RemoteSpineEngineManager2.run() Sending data: %s"%jsonTxt)

                jsonTxt=json.dumps(jsonTxt)
                print("RemoteSpineEngineManager2.run() Data after conversion: %s"%jsonTxt)
 
                #get folder from input data, and package it
                print("RemoteSpineEngineManager2.run() Packaging folder %s.."%self._inputData['project_dir'])
                FilePackager.package(self._inputData['project_dir'],self._inputData['project_dir']+"/",RemoteSpineEngineManager2.ZipFileName)
                            
                #send request to the remote client, and listen for a response
                dataEvents=self.zmqClient.send(jsonTxt,self._inputData['project_dir']+"/",RemoteSpineEngineManager2.ZipFileName+".zip")
                print("RemoteSpineEngineManager2.run() received a response:")
                print(dataEvents)
                print("RemoteSpineEngineManager2.run() %d of event+data items received."%len(dataEvents))
                self._outputData=dataEvents
                self._outputDataIteratorIndex=0

                #remove the transferred ZIP-file
                FilePackager.deleteFile(self._inputData['project_dir']+"/"+RemoteSpineEngineManager2.ZipFileName+".zip")

                #change state to REPLY_RECEIVED
                self._state=RemoteSpineEngineManagerState2.REPLY_RECEIVED
                self._requestPending=False

            else:
                time.sleep(0.01)

        print("RemoteSpineEngineManager2.run()..out")


    def _addQuotesToDictString(self,str):
        newStr=str.replace('\': <','\': \'')
        retStr=newStr.replace('}','\'}')
        return retStr

#RemoteSpineEngineManager("tcp","193.166.160.216",44343)
