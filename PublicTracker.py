import json
import socket
import threading
import sqlite3
import os
from UserFunctions import UserFunctions


class PublicTracker:
    ip = "0.0.0.0"
    port = 6987

    def __init__(self, trackerName, trackerDescription, trackerOwner):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_CONNECTIONS = 1500
        self.serverAlive = False
        self.trackerInfo = {"trackerName": trackerName, "trackerDescription": trackerDescription,
                            "trackerOwner": trackerOwner}

    def StartPublicTracker(self):
        """
        Start the public tracker.
        :return: Nothing
        """
        # Checking for the file database
        if not os.path.isfile("Databases/files.db"):  # Checking if the file's database exists.
            open("Databases/files.db", "x")
            newFilesConnection = sqlite3.connect("Databases/files.db")
            filesCurser = newFilesConnection.cursor()

            filesCurser.execute("""CREATE TABLE files (
                    id INTEGER PRIMARY KEY,
                    fileName TEXT,
                    fileSize INTEGER,
                    pieceSize INTEGER,
                    amountOfPieces INTEGER,
                    fileVisibility TEXT,
                    fileOwners TEXT,
                    fileUploader TEXT
            )""")

            newFilesConnection.commit()
            newFilesConnection.close()
        try:  # Starting the server
            self.serverSocket.bind((self.ip, self.port))
            self.serverSocket.listen(self.MAX_CONNECTIONS)
            self.serverAlive = True
            while self.serverAlive:
                clientSocket, addr = self.serverSocket.accept()
                threading.Thread(target=self.ServerLoop, args=[clientSocket, addr]).start()
        except Exception as e:
            self.serverAlive = False
            print("Couldn't start the public tracker. Here is the error log: {}".format(e))

    def ServerLoop(self, clientSocket, addr):
        """
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :param addr: The address of the peer.
        :return: Nothing
        """
        peerInterested = True
        print("A new connection is made with: {}".format(addr))
        while peerInterested:
            try:
                jsonData = clientSocket.recv(1024).decode()
                if jsonData:
                    dataFromPeer = json.loads(jsonData)
                    # check if the user exists
                    if not UserFunctions.user_exists(dataFromPeer["userID"], dataFromPeer["firstName"],
                                                     dataFromPeer["lastName"], dataFromPeer["email"],
                                                     dataFromPeer["rank"]):
                        clientSocket.send(json.dumps({"errorMessage": "Verification failed with this user"}).encode())
                        peerInterested = False
                        continue
                    match dataFromPeer["requestType"]:
                        case 0:
                            # get all files from the database.
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            match dataFromPeer["rank"]:
                                case "admin":
                                    filesCurser.execute("SELECT * FROM files")
                                case "manager":
                                    filesCurser.execute("SELECT * FROM files WHERE NOT fileVisibility = 'admin'")
                                case "worker":
                                    filesCurser.execute(
                                        "SELECT * FROM files WHERE NOT fileVisibility = 'admin' AND NOT fileVisibility = 'manager'")
                                case "visitor":
                                    filesCurser.execute(
                                        "SELECT * FROM files WHERE NOT fileVisibility = 'admin' AND NOT fileVisibility = 'manager' AND NOT fileVisibility = 'worker'")
                                case _:
                                    filesCurser.execute("SELECT * FROM file WHERE fileVisibility = 'fuck you'")

                            allFiles = filesCurser.fetchall()
                            clientSocket.send(json.dumps(allFiles).encode())
                        case 1:
                            #upload a new file
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            filesCurser.execute("INSERT INTO files ()")
                        case 2:
                            pass
                        case 3:
                            # user finished downloading a file
                            pass
                        case 4:
                            # delete a file from the database
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            filesCurser.execute("SELECT * FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            file = filesCurser.fetchall()[0]

                            if file[1] != dataFromPeer["fileName"]:  # Checking that the file id and name match
                                clientSocket.send(
                                    json.dumps({"errorMessage": "file name doesnt match with the database"}).encode())
                                peerInterested = False
                                continue

                            uploader = "{}:{}:{}:{}:{}".format(dataFromPeer["userID"], dataFromPeer["firstName"],
                                                               dataFromPeer["lastName"], dataFromPeer["email"],
                                                               dataFromPeer["rank"])
                            if uploader != file[7]:  # This means the user that sent the request isn't the uploader and he cant delete the file
                                clientSocket.send(json.dumps(
                                    {"errorMessage": "original uploader and request uploader arent matching"}).encode()
                                )
                                peerInterested = False
                                continue

                            filesCurser.execute("DELETE FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            filesConnection.commit()
                            filesConnection.close()
                            clientSocket.send(json.dumps({"status": "success"}).encode())
                        case 5:
                            # kill connection with the tracker
                            peerInterested = False
                        case 6:
                            # get the tracker info
                            clientSocket.send(json.dumps(self.trackerInfo).encode())
                        case _:
                            print("got a unknown requestType. reminder: this is a PUBLIC tracker.")
            except Exception as e:
                peerInterested = False
                print("Something went wrong on the server loop. dropping the connection " + str(e))


t = PublicTracker("IdoTracker", "TestTracker", "Ido")
t.StartPublicTracker()
