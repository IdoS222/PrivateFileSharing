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
                threading.Thread(target=self.ServerLoop, args=[clientSocket, addr]).start()
        except Exception as e:
            self.serverAlive = False
            print("Couldn't start the server. " + str(e))

    def ServerLoop(self, clientSocket, addr):
        """
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :param addr: The address of the peer.
        :return: Nothing
        """
        peerInterested = True
        while peerInterested:
            dataFromPeer = self.ProcessRequest(clientSocket.recv(1024).decode())
            if dataFromPeer:
                if dataFromPeer[0] == "downloadPart":
                    # logic for sending a file
                    try:
                        pathToFile = r"{}\{}".format(self.filesFolder, dataFromPeer[1])  # The path to the file
                        with open(pathToFile, 'r') as file:  # opening the file
                            file.seek(int(dataFromPeer[3]) * int(dataFromPeer[5]))  # jumping to the part of the file, the peer is interested in.
                            index = 0
                            data = ""
                            while index < int(dataFromPeer[3]):  # reading only the part we need and stopping after we finish reading it
                                data += file.read(index)
                                index += 1
                            clientSocket.send(data.encode())
                    except Exception:
                        print("Couldn't send the file to the peer.")
                        clientSocket.send("False".encode())
                elif dataFromPeer[0] == "killConnection":
                    peerInterested = False
                else:
                    # we got a unique request, so we are dropping the connection
                    peerInterested = False

    def KillServer(self):
        """
        Kill the server
        :return: Nothing
        """
        self.serverAlive = False

    def ProcessRequest(self, request):
        """
        Parsing the request into a list.
        :param request: The request from the peer
        :return: A list of all the variables the request contains
        """
        listOfVariables = list()
        currentWord = ""
        index = 0
        while index < len(request):
            if request[index] == "_":
                listOfVariables.append(currentWord)
                word = ""
                index += 1
                continue
            currentWord += request[index]
            index += 1

        return listOfVariables