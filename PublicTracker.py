import json
import socket
import threading
import sqlite3
import os
from SocketFunctions import SocketFunctions


class PublicTracker:
    ip = "0.0.0.0"
    port = 6987
    usersServerLocation = ("127.0.0.1", 29574)

    def __init__(self, trackerName="Unknown", trackerDescription="Unknown", trackerOwner="Unknown"):
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
                    fileUploader TEXT,
                    listOfHashes TEXT
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
                jsonData = SocketFunctions.read_from_socket(clientSocket)
                if jsonData:
                    dataFromPeer = json.loads(jsonData)
                    # check if the user exists
                    usersSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    usersSocket.connect(self.usersServerLocation)

                    SocketFunctions.send_data(usersSocket, json.dumps({
                        "requestType": "userExist",
                        "userID": dataFromPeer["userID"],
                        "firstName": dataFromPeer["firstName"],
                        "lastName": dataFromPeer["lastName"],
                        "email": dataFromPeer["email"],
                        "rank": dataFromPeer["rank"]
                    }))

                    existsJson = SocketFunctions.read_from_socket(usersSocket)
                    existsDict = json.loads(existsJson)

                    try:  # Checking if the user is a real user.
                        if existsDict["status"] != "The user exists":
                            SocketFunctions.send_data(clientSocket, (
                                json.dumps({"errorMessage": "Verification failed with this user"})))
                            peerInterested = False
                            continue
                    except KeyError:
                        SocketFunctions.send_data(clientSocket, json.dumps({"errorMessage": "Verification failed with this user"}))
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
                            SocketFunctions.send_data(clientSocket, json.dumps(allFiles))
                        case 1:
                            # upload a new file
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            if dataFromPeer["fileSize"] > 1000000000:  # The file size limit for now is 1 GB
                                SocketFunctions.send_data(clientSocket,
                                    json.dumps({
                                        "errorMessage": "piece size times the amount of pieces doesnt equals to the file size."}))
                                continue

                            if dataFromPeer["pieceSize"] * dataFromPeer["amountOfPieces"] != dataFromPeer["fileSize"]:
                                SocketFunctions.send_data(clientSocket,
                                    json.dumps({
                                        "errorMessage": "piece size times the amount of pieces doesnt equals to the file size."}))
                                continue
                            filesCurser.execute(
                                "INSERT INTO files (fileName, fileSize, pieceSize, amountOfPieces, fileVisibility, fileOwners, fileUploader, listOfHashes) "
                                "VALUES ('{}', {}, {}, {}, '{}', '{}', '{}')".format(dataFromPeer["fileName"],
                                                                                     dataFromPeer["fileSize"],
                                                                                     dataFromPeer["pieceSize"],
                                                                                     dataFromPeer["amountOfPieces"],
                                                                                     dataFromPeer["fileVisibility"],
                                                                                     dataFromPeer["fileOwners"],
                                                                                     dataFromPeer["fileUploader"]),
                                                                                    dataFromPeer["listOfHashes"])
                            filesConnection.commit()
                            filesConnection.close()
                            SocketFunctions.send_data(clientSocket, json.dumps({"status": "The file entered the database"}))
                        case 2:
                            # A user is stating a download and requesting the list of peers and a list of hashes
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            filesCurser.execute("SELECT * FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            file = filesCurser.fetchall()[0]

                            if file[1] != dataFromPeer["fileName"]:  # Checking that the file id and name match
                                SocketFunctions.send_data(clientSocket,
                                    json.dumps({"errorMessage": "file name doesnt match with the database"}))
                                continue

                            SocketFunctions.send_data(clientSocket, json.dumps({"Peers": file[6], "listOfHashes": file[8]}))
                        case 3:
                            # user finished downloading a file
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            filesCurser.execute("SELECT * FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            file = filesCurser.fetchall()[0]

                            if file[1] != dataFromPeer["fileName"]:  # Checking that the file id and name match
                                SocketFunctions.send_data(clientSocket,
                                    json.dumps({"errorMessage": "file name doesnt match with the database"}))
                                continue

                            previousOwners = json.loads(file[6])  # getting the owners
                            owner = (addr[0], 15674)
                            newOwners = json.dumps(previousOwners.append(owner))
                            filesConnection.execute("UPDATE files SET fileOwners = '{}' WHERE id = {}".format(newOwners,
                                                                                                              dataFromPeer[
                                                                                                                  "fileID"]))
                            filesConnection.commit()
                            filesConnection.close()
                            SocketFunctions.send_data(clientSocket, json.dumps({"status": "success"}))
                        case 4:
                            # delete a file from the database
                            filesConnection = sqlite3.connect("Databases/files.db")
                            filesCurser = filesConnection.cursor()

                            filesCurser.execute("SELECT * FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            file = filesCurser.fetchall()[0]

                            if file[1] != dataFromPeer["fileName"]:  # Checking that the file id and name match
                                SocketFunctions.send_data(clientSocket,
                                    json.dumps({"errorMessage": "file name doesnt match with the database"}))
                                continue

                            uploader = "{}:{}:{}:{}:{}".format(dataFromPeer["userID"], dataFromPeer["firstName"],
                                                               dataFromPeer["lastName"], dataFromPeer["email"],
                                                               dataFromPeer["rank"])
                            if uploader != file[7]:  # This means the user that sent the request isn't the uploader
                                # and he cant delete the file
                                SocketFunctions.send_data(clientSocket, json.dumps(
                                    {"errorMessage": "original uploader and request uploader arent matching"}))
                                continue
                            filesCurser.execute("DELETE FROM files WHERE id = {}".format(dataFromPeer["fileID"]))
                            filesConnection.commit()
                            filesConnection.close()
                            SocketFunctions.send_data(clientSocket, json.dumps({"status": "success"}))
                        case 5:
                            # kill connection with the tracker
                            peerInterested = False
                        case 6:
                            # get the tracker info
                            SocketFunctions.send_data(clientSocket, json.dumps(self.trackerInfo))
                        case _:
                            print("got a unknown requestType. reminder: this is a PUBLIC tracker.")
            except KeyError as e:
                # This means that we got an illegal request.
                print(e)
                SocketFunctions.send_data(clientSocket, json.dumps({"errorMessage": "Couldn't send the data"}))
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


t = PublicTracker()
t.StartPublicTracker()
