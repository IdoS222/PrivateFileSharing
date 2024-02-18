import json
import socket
import threading


class PeerServer:
    ip = "0.0.0.0"
    port = 15674
    filesFolder = r"C:\Users\Owner\Desktop\Test"

    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_CONNECTIONS = 1500
        self.serverAlive = False
        self.StartPeerServer()

    def StartPeerServer(self):
        """
        Start the server and start waiting for connection
        :return: Nothing
        """
        try:
            self.serverSocket.bind((self.ip, self.port))
            self.serverSocket.listen(self.MAX_CONNECTIONS)
            self.serverAlive = True
            while self.serverAlive:
                clientSocket, addr = self.serverSocket.accept()
                print("new connection is made with {}".format(addr))
                threading.Thread(target=self.ServerLoop, args=[clientSocket, ]).start()
        except Exception as e:
            self.serverAlive = False
            print("Couldn't start the server. " + str(e))

    def ServerLoop(self, clientSocket):
        """
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :return: Nothing
        """
        peerInterested = True
        while peerInterested:
            try:
                data = clientSocket.recv(1024).decode()
                if data:
                    dataFromPeer = json.loads(data)
                    if dataFromPeer["requestType"] == "downloadPart":
                        # logic for sending a file
                        pathToFile = r"{}\{}".format(self.filesFolder, dataFromPeer["fileName"])  # The path to the file
                        with open(pathToFile, 'rb') as file:  # opening the file
                            file.seek(int(dataFromPeer["pieceNumber"]) * int(dataFromPeer[
                                                                                 "pieceSize"]))  # jumping to the part of the file, the peer is interested in.
                            index = 0
                            data = b""
                            while index < dataFromPeer[
                                "pieceSize"]:  # reading only the part we need and stopping after we finish reading it
                                data += file.read(index)
                                index += 1
                            clientSocket.send(json.dumps({"data": str(data)}).encode())
                            print("done")
                    elif dataFromPeer["requestType"] == "killConnection":
                        peerInterested = False
                    else:
                        # we got a unique request, so we are dropping the connection
                        peerInterested = False
                else:
                    continue
            except KeyError as e:
                # This means that we got an illegal request.
                print(e)
                clientSocket.send(json.dumps({"errorMessage": "Couldn't send the data"}).encode())
                peerInterested = False
            except ConnectionResetError as e:
                # This means that something is wrong with the connection and we cant send an error message since it would throw another exception.
                print(e)
                peerInterested = False
            except Exception as e:
                # General exception just in case somthing unexpected happened
                print(e)
                peerInterested = False


p = PeerServer()
