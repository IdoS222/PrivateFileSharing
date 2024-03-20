import json
import socket
from flask import Flask, request
from TrackerRequests import TrackerRequest
import os
from SocketFunctions import SocketFunctions
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # check if needed
filesFolder = os.path.join(os.getenv('LOCALAPPDATA'), "PFS")
webServerLocation = ("127.0.0.1", 80)


@app.route('/pieceData', methods=['GET'])
def pieceData():
    userRaw = request.args.get("user")
    user = json.loads(userRaw)
    if user is None or not isinstance(user, dict):  # Checking if we got the user and if he is a dict object
        return "Didn't get the user or the user is not in a dict object"

    httpRequest = "GET userExists?" + json.dumps(user)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(webServerLocation)
    sock.send(httpRequest.encode())

    userExists = SocketFunctions.read_from_socket(sock)
    return userExists


@app.route('/downloadFile')
def downloadFile():
    pass


app.run(host="0.0.0.0", port=15674)


def download_file(user, tracker, fileID, fileName, amountOfPieces, pieceSize):
    dataFromTracker = TrackerRequest.start_download(tracker, user, fileID, fileName)
    try:
        peerList = dataFromTracker["Peers"]
        hashList = dataFromTracker["listOfHashes"]["hashes"]
        answerList = []
        for pieceNum in range(amountOfPieces):  # TODO: Multi process
            download_piece_from_peer(peerList, pieceNum, pieceSize, fileName, filesFolder, hashList, answerList)
        for answer in answerList:
            if not answer:
                # If one of the answers is false, it means we didn't download one of the pieces.
                # Notify the user and return
                return False
        # The process of merging all the files.
        fileData = b''
        # Merge all the small files to one large file.
        for piece in range(amountOfPieces):
            with open("{}/{}{}".format(filesFolder, piece, fileName), "rb") as pieceFile:
                pieceData = pieceFile.read()
            fileData += pieceData
            os.remove("{}/{}{}".format(filesFolder, piece, fileName))
        with open("{}/{}".format(filesFolder, fileName), "wb") as file:
            file.write(fileData)
        return True
    except KeyError:  # This error means we didn't get the peers and hashes from the tracker,
        # but instead we got a error message
        # TODO: notify the user we couldn't connect to the tracker.
        print(dataFromTracker["errorMessage"])
        return False
    except Exception:  # General exception just in case
        # TODO: notify the user that something went wrong.
        # TODO: maybe make a file with the error message or something? idk
        return False


def download_piece_from_peer(owners, pieceNum, pieceSize, fileName, path, hashlist, answerList):
    try:
        for owner in owners:  # TODO: get random peer.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((owner, 15674))
            pieceRequest = {
                "requestType": "downloadPart",
                "pieceNumber": pieceNum,
                "pieceSize": pieceSize,
                "fileName": fileName
            }
            SocketFunctions.send_data(sock, json.dumps(pieceRequest))
            dataFromPeer = SocketFunctions.read_from_socket(sock)
            jsonData = json.loads(dataFromPeer)
            sock.close()
            chuckData = base64.b64decode(jsonData["data"])
            # Validate the piece
            chuckHash = hashlib.sha256(chuckData).hexdigest()
            if chuckHash != hashlist[pieceNum]:
                # We didn't get the correct data from the piece, and we need to download it from another peer.
                continue
            else:
                with open("{}/{}{}".format(path, pieceNum, fileName), "wb") as file:
                    subprocess.run(["attrib", "+H", "{}/{}{}".format(path, pieceNum, fileName)], check=True)
                    file.write(chuckData)
                    answerList.append(True)
                    return True
        # If we couldn't download the piece from any owner, we will return false
        answerList.append(False)
        return False
    except Exception as e:  # If there is an exception, we will return false
        print(e)
        answerList.append(False)
        return False


"""

class PeerServer:
    filesFolder = os.path.join(os.getenv('LOCALAPPDATA'), "PFS")

    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_CONNECTIONS = 1500
        self.serverAlive = False

    def start_peer_server(self):
        checking for the files folder and creating it if the folder is absent and then starting the server and start waiting for connection
        :return: Nothing

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
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :return: Nothing
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
                            while index < dataFromPeer[
                                "pieceSize"]:  # reading only the part we need and stopping after we finish reading it
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

"""
