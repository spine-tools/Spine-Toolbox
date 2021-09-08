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
Parser for JSON-based messages exchanged between server and clients.
:authors: P. Pääkkönen (VTT)
:date:   25.08.2021
"""

import json
from spinetoolbox.server.util.ServerMessage import ServerMessage

class ServerMessageParser:
  
    @staticmethod
    def parse(message):
        """
        Args:
            message: JSON-message as a string
        Returns:
            Parsed message as a ServerMessage
        """
        if message==None:
            raise ValueError("invalid input to ServerMessageParser.parse()")
        if len(message)==0:
            raise ValueError("invalid input to ServerMessageParser.parse()")

        parsedMsg=json.loads(message)
        #print("ServerMessageParser.parse() parsed msg type:")
        #print(parsedMsg)
        fileNames=parsedMsg['files']
        #print("number of file names: %d"%len(fileNameStr))

        #parse file names
        #print("ServerMessageParser.parse() type of data: ")
        #print(type(json.dumps(parsedMsg['data'])))
        #dataStr=json.dumps(parsedMsg['data'])
        dataStr=parsedMsg['data']
        #print("ServerMessageParser.parse() Data: %s"%dataStr)

        parsedFileNames=[]
        if len(fileNames)>0:
            for f in fileNames:
                #print(fileNames[f])
                parsedFileNames.append(fileNames[f])
            msg=ServerMessage(parsedMsg['command'],parsedMsg['id'],dataStr,parsedFileNames)
        else:
            msg=ServerMessage(parsedMsg['command'],parsedMsg['id'],dataStr,None)
        return msg
