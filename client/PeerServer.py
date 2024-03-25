import json
import os
import socket
import threading
import base64
from SocketFunctions import SocketFunctions


class PeerServer:
    filesFolder = os.path.join(os.getenv('LOCALAPPDATA'), "PFS")

    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_CONNECTIONS = 1500
        self.serverAlive = False

    def start_peer_server(self):
        """
        checking for the files folder and creating it if the folder is absent and then starting the server and start waiting for connection
        :return: Nothing
        """

        if os.path.isdir(os.path.join(os.getenv('LOCALAPPDATA'), "PFS")):
            # The folder is already created, and we can move on and start the server
            pass
        else:
            os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'), "PFS"))

        try:
            self.serverSocket.bind(("0.0.0.0", 15674))
            self.serverSocket.listen(self.MAX_CONNECTIONS)
            self.serverAlive = True
            while self.serverAlive:
                clientSocket, addr = self.serverSocket.accept()
                threading.Thread(target=self.server_loop, args=[clientSocket, ]).start()
        except Exception as e:
            self.serverAlive = False
            print("Couldn't start the server. " + str(e))

    def server_loop(self, clientSocket):
        """
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :return: Nothing
        """
        peerInterested = True
        while peerInterested:
            try:
                data = SocketFunctions.read_from_socket(clientSocket)
                if data:
                    dataFromPeer = json.loads(data)
                    if dataFromPeer["requestType"] == "downloadPart":
                        # logic for sending a file
                        pathToFile = os.path.join(self.filesFolder, dataFromPeer["fileName"])  # The path to the file
                        with open(pathToFile, 'rb') as file:  # opening the file
                            file.seek(int(dataFromPeer["pieceNumber"]) * int(dataFromPeer[
                                                                            "pieceSize"]))  # jumping to the part of the file, the peer is interested in.
                            index = 0
                            data = b''
                            while index < dataFromPeer["pieceSize"]:  # reading only the part we need and stopping after we finish reading it
                                data += file.read(1)
                                index += 1
                            jsonDump = json.dumps({"data": (base64.b64encode(data)).decode('utf8')})
                            SocketFunctions.send_data(clientSocket, jsonDump)
                    elif dataFromPeer["requestType"] == "killConnection":
                        peerInterested = False
                else:
                    continue
            except KeyError as e:
                # This means that we got an illegal request.
                print(e)
                SocketFunctions.send_data(clientSocket, json.dumps({"errorMessage": "Got an illegal request"}).encode())
                peerInterested = False
            except ConnectionResetError as e:
                # This means that something is wrong with the connection and we cant send an error message since it
                # would throw another exception.
                print(e)
                peerInterested = False
            except Exception as e:
                # General exception just in case something unexpected happened
                print(e)
                peerInterested = False


p = PeerServer()
p.start_peer_server()
