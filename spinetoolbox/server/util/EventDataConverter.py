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
Contains a helper class for converting received event/data information to JSON-based format
:authors: P. Pääkkönen (VTT)
:date:   27.08.2021
"""

import base64
import json


class EventDataConverter:


    """
    Converts events+data
    Args:
        eventData(a list of tuples containing events and data)
    Return:
        JSON string
    """
    @staticmethod
    def convert(eventData):
        itemCount=len(eventData)
        i=0
        retStr="{\n"
        retStr+="    \"items\": [\n"
        for ed in eventData:
            #print(ed)
            #convert data to Base64
            msgBytes=str(ed[1]).encode('ascii')
            base64Bytes=base64.b64encode(msgBytes)
            base64Data=base64Bytes.decode('ascii')

            retStr+="    {\n        \"event_type\": \""+ed[0]+"\",\n"
            if (i+1) < itemCount:
                retStr+="        \"data\": \""+base64Data+"\"\n    },\n"
                #print("orig dict:")
                #print(ed[1])
                #print("modified to str:")
                #print(str(ed[1]))
            else:
                retStr+="        \"data\": \""+base64Data+"\"\n    }\n"
            i+=1
        retStr+="    ]\n"
        retStr+="}\n"
        return retStr


    """
    Converts JSON to events+data
    Args:
        jsonStr(str): events+data as JSON
        base64Data(Boolean):flag indicating, when data is encoded into Base64 
    Return:
        a list of tuples containing events and data
    """
    @staticmethod
    def convertJSON(jsonStr,base64Data):
        parsedJSON=json.loads(jsonStr)
        #print(parsedJSON)
        itemsList=parsedJSON['items']
        #print("parsed list of items:")
        #print(itemsList)
        retList=[]
        for item in itemsList:
            #print(item['event_type'])
            #print(item['data'])
            if base64Data==False:
                retList.append((item['event_type'],item['data']))
            else: #decode Base64
                base64_bytes=item['data'].encode('ascii')
                message_bytes = base64.b64decode(base64_bytes)
                decodedData = message_bytes.decode('ascii')
                retList.append((item['event_type'],decodedData))
        return retList 


