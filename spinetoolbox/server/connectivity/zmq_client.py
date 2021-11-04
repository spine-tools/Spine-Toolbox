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
A Zero-MQ client for exchanging messages between the toolbox client and the remote server.
:author: P. Pääkkönen (VTT)
:date:   02.09.2021
"""

import os
import zmq
import zmq.auth
import json
import time
import random
from enum import unique, Enum
from spine_engine.server.util.server_message import ServerMessage
from spine_engine.server.util.server_message_parser import ServerMessageParser
from spine_engine.server.util.event_data_converter import EventDataConverter


@unique
class ZMQSecurityModelState(Enum):
    NONE = 0  # no security is used
    STONEHOUSE = 1  # stonehouse-security model of Zero-MQ


# used, when connectivity is tested during initialisation
@unique
class ZMQClientConnectionState(Enum):
    CONNECTED = 0
    DISCONNECTED = 1


class ZMQClient:
    def __init__(self, protocol, remoteHost, remotePort, secModel, secFolder):
        """
        Args:
            protocol (string): Zero-MQ protocol
            remoteHost: location of the remote spine server
            remotePort(int): port of the remote spine server
            secModel: see: ZMQSecurityModelState
            secFolder: folder, where security files have been stored.
        """
        self.connectivity_testing = True

        if secModel == ZMQSecurityModelState.NONE:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.setsockopt(zmq.LINGER, 1)
            ret = self._socket.connect(protocol + "://" + remoteHost + ":" + str(remotePort))
            # print(f"ZMQClient(): socket.connect() return value: {ret}")
            # print("ZMQClient(): Connection established to %s:%d" % (remoteHost, remotePort))
        elif secModel == ZMQSecurityModelState.STONEHOUSE:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.setsockopt(zmq.LINGER, 1)
            # security configs
            # implementation below based on https://github.com/zeromq/pyzmq/blob/main/examples/security/stonehouse.py
            # prepare folders
            base_dir = secFolder
            # base_dir = os.path.dirname("/home/ubuntu/sw/spine/dev/zmq_server_certs/")
            # print("ZMQClient(): security folder %s"%base_dir)
            secret_keys_dir = os.path.join(base_dir, 'private_keys')
            keys_dir = os.path.join(base_dir, 'certificates')
            public_keys_dir = os.path.join(base_dir, 'public_keys')

            # We need two certificates, one for the client and one for
            # the server. The client must know the server's public key
            # to make a CURVE connection.

            client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
            client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
            self._socket.curve_secretkey = client_secret
            self._socket.curve_publickey = client_public

            # The client must know the server's public key to make a CURVE connection.
            server_public_file = os.path.join(public_keys_dir, "server.key")
            server_public, _ = zmq.auth.load_certificate(server_public_file)
            self._socket.curve_serverkey = server_public

            ret = self._socket.connect(protocol + "://" + remoteHost + ":" + str(remotePort))
            # print("ZMQClient(): socket.connect() return value: %d"%ret)
            # print("ZMQClient(): Connection established with security to %s:%d"%(remoteHost,remotePort))
        # test connectivity
        if self.connectivity_testing:
            connected = self._check_connectivity(1000)
            if connected:
                self._connection_state = ZMQClientConnectionState.CONNECTED
            else:
                self._connection_state = ZMQClientConnectionState.DISCONNECTED

        else:
            self._connection_state = ZMQClientConnectionState.CONNECTED
        self._closed = False  # for tracking multiple closing calls

    def getConnectionState(self):
        """
        Returns connection state
        Returns:
            ZMQClientConnectionState
        """
        return self._connection_state

    def send(self, text, fileLocation, fileName):
        """
        Args:
            text (string): 
            fileLocation (string): location of the binary file to be transferred
            fileName (string): name of the binary file to be transferred

        Returns:
            a list of tuples containing events+data
        """
        # check if folder and file exist
        # print("ZMQClient.send(): path %s exists: %s file %s exists: %s." % (fileLocation, os.path.isdir(fileLocation), fileName, os.path.exists(fileLocation+fileName)))
        if not os.path.isdir(fileLocation) or not os.path.exists(os.path.join(fileLocation, fileName)):
            # print("ZMQClient.send(): invalid path or file.")
            raise ValueError("invalid path or file.")
        if not text:
            raise ValueError("invalid input text")
        # Read file content
        f = open(os.path.join(fileLocation, fileName), 'rb')
        fileData = f.read()
        f.close()
        # create message content
        randomId = random.randrange(10000000)
        msg_parts = []
        listFiles = [fileName]
        msg = ServerMessage("execute", str(randomId), text, listFiles)
        print("ZMQClient(): msg to be sent : %s" % msg.toJSON())
        part1Bytes = bytes(msg.toJSON(), 'utf-8')
        msg_parts.append(part1Bytes)
        msg_parts.append(fileData)
        # transfer
        self._socket.send_multipart(msg_parts)
        # print("ZMQClient(): listening to a reply.")
        message = self._socket.recv()
        # decode
        msgStr = message.decode('utf-8')
        # print("ZMQClient()..Received reply %s" %msgStr)
        parsedMsg = ServerMessageParser.parse(msgStr)
        # get and decode events+data
        data = parsedMsg.getData()
        # print(type(data))
        jsonData = json.dumps(data)
        dataEvents = EventDataConverter.convertJSON(jsonData, True)
        return dataEvents

    def close(self):
        if not self._closed:
            self._socket.close()
            self._context.term()
            print("ZMQClient(): Connection closed.")
            self._closed = True
        else:
            print("ZMQClient(): Connection was closed before.")

    def _check_connectivity(self, timeout):
        """
        Args:
            timeout (int): Time to wait before giving up [ms]
        """
        startTimeMs = round(time.time() * 1000.0)  # debugging
        msg_parts = []
        randomId = random.randrange(10000000)
        pingMsg = ServerMessage("ping", str(randomId), "", None)
        pingAsJson = pingMsg.toJSON()
        pingInBytes = bytes(pingAsJson, 'utf-8')
        msg_parts.append(pingInBytes)
        sendRet = self._socket.send_multipart(msg_parts, flags=zmq.NOBLOCK)
        event = self._socket.poll(timeout=timeout)
        if event == 0:
            print("ZMQClient._check_connectivity(): timeout occurred, no reply will be listened to")
            return False
        else:
            msg = self._socket.recv()
            msgStr = msg.decode("utf-8")
            stopTimeMs = round(time.time() * 1000.0)  # debugging
            print("ZMQClient._check_connectivity(): ping message was received, RTT: %d ms" % (stopTimeMs - startTimeMs))
            return True
