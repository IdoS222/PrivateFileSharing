import base64
import json
import random
import socket
import threading
import hashlib
from tkinter import filedialog
import flask_login
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect, jsonify
import os
import subprocess
from User import User
from TrackerRequests import TrackerRequest
from PeerServer import PeerServer
import ipaddress
from SocketFunctions import SocketFunctions
from tkinter import Tk
import math

app = Flask(__name__, template_folder=os.path.join("www", "templates"),
            static_folder=os.path.join("www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)
login_manager.session_protection = "strong"
filesFolder = r"C:\Users\Owner\Desktop\Test"
usersServerLocation = ("127.0.0.1", 29574)
activeUser = None


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/application', methods=['GET'])
@flask_login.login_required
def application():
    if flask_login.current_user.__dict__["tracker"] != "No":
        trackerInfoAndFiles = TrackerRequest.get_files_and_info_from_tracker(flask_login.current_user.__dict__["tracker"], flask_login.current_user.__dict__)
        if len(trackerInfoAndFiles) == 1:
            # The only reason this list is of len 1 is that we got an error message.
            return render_template("applicationNoTracker.html", errorMessage=trackerInfoAndFiles[0]["errorMessage"])
        return render_template("application.html", files=trackerInfoAndFiles[0],
                               trackerInfo=trackerInfoAndFiles[1])
    else:
        # There is no active tracker and we need to notify the user.
        return render_template("applicationNoTracker.html",
                               errorMessage="There is no active tracker! please connect to a tracker from the settings page.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")

    try:  # trying to see if all the values we expected arrived.
        x = request.values["firstName"]
        x = request.values["lastName"]
        x = request.values["email"]
        x = request.values["password"]
        x = request.values["confirmPassword"]
    except KeyError:
        # In this case, the values we wanted didn't arrive, and we need to do something about it (they think they are
        # tough, we are tougher)
        return render_template("tough_guy.html")  # TODO: ERROR MESSAGE
    
    try:
        # Trying to register the user in the database after verifying the values we got.
        userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        userSocket.connect(usersServerLocation)
        SocketFunctions.send_data(userSocket, json.dumps({  # This is the request for registering a new user
            "requestType": "registerUser",
            "firstName": request.values["firstName"],
            "lastName": request.values["lastName"],
            "email": request.values["email"],
            "password": request.values["password"],
            "confirmPassword": request.values["confirmPassword"],
            "rank": "visitor"
        }))
        data = SocketFunctions.read_from_socket(userSocket)
        jsonStatus = json.loads(data)
        userSocket.close()
        return jsonify(jsonStatus)
    except Exception:
        return jsonify({"errorMessage": "couldent connect to the users server."})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # Validating the login request we got.
    try:
        x = request.values["email"]
        x = request.values["password"]
    except KeyError:
        return render_template("tough_guy.html")  # TODO: ERROR MESSAGE
    try:
        userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        userSocket.connect(usersServerLocation)
        SocketFunctions.send_data(userSocket, json.dumps({  # This is the request for registering a new user
            "requestType": "processLogin",
            "email": request.values["email"],
            "password": request.values["password"],
        }))

        data = SocketFunctions.read_from_socket(userSocket)
        loginJsonStatus = json.loads(data)

        SocketFunctions.send_data(userSocket, json.dumps({  # This is the request for getting the user info
            "requestType": "getUserInfo",
            "email": request.values["email"],
        }))

        data = SocketFunctions.read_from_socket(userSocket)
        userInfoStatus = json.loads(data)
        userSocket.close()
        if "status" in loginJsonStatus:
            if "status" in userInfoStatus:
            # If we got here we also got the info from the server, and we can finally log in
                    user = userInfoStatus["status"]  # The list of all the user info
                    # Update the active tracker
                    tracker = "No"
                    if user[5] != "No":
                        trackerDict = json.loads(user[5])
                        tracker = [trackerDict["ip"], trackerDict["port"]]
                    flask_login.login_user(User(user[0], user[1], user[2], user[3], user[4], tracker),remember=True)
                    return redirect('/application')
            else:
                return jsonify(userInfoStatus)
        else:
            return jsonify(loginJsonStatus)
    except Exception:
        return jsonify({"errorMessage": "couldent connect to the users server."})

@login_manager.user_loader
def load_user(user_email):
    # Search user email in db
    try:
        userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        userSocket.connect(usersServerLocation)
        SocketFunctions.send_data(userSocket, json.dumps({  # This is the request for registering a new user
            "requestType": "getUserInfo",
            "email": user_email,
        }))

        data = SocketFunctions.read_from_socket(userSocket)
        jsonStatus = json.loads(data)
        userSocket.close()
        if "status" in jsonStatus.keys():
            found_user = jsonStatus["status"]
            if found_user[5] == "No":
                return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],
                            "No")
            tracker = json.loads(found_user[5])
            return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],
                        (tracker["ip"], tracker["port"]))
        else:
            return None
    except Exception:
        return None


@login_manager.unauthorized_handler
def unauthorized_callback():  # This handler is called when trying to access the application page without a login session.
    pass #TODO: do something here


@app.route("/logout", methods=['POST'])
def logout():  # handling the logout
    flask_login.logout_user()
    return redirect("/login")


@app.route("/settings", methods=["GET", "POST"])
@flask_login.login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")

    try:
        x = request.values["ipAddress"]
        ipObj = ipaddress.ip_address(request.values["ipAddress"])
    except KeyError as e:
        return jsonify({"errorMessage": e})
    except ValueError:
        # The ip given is not an ip address.
        return jsonify({"errorMessage": "Ip address isn't valid."})

    try:
        usersSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        usersSocket.connect(usersServerLocation)

        SocketFunctions.send_data(usersSocket, json.dumps({
            "requestType": "changeTracker",
            "email": flask_login.current_user.__dict__["email"],
            "tracker": json.dumps({"ip": request.values["ipAddress"], "port": 6987})
        }))

        data = SocketFunctions.read_from_socket(usersSocket)
        jsonData = json.loads(data)
        usersSocket.close()

        if "status" in jsonData.keys():
            if jsonData["status"] == "tracker set":
                flask_login.current_user.__dict__["tracker"] = [(request.values["ipAddress"], int(request.values["port"]))]

        return jsonify(jsonData)
    except Exception:
        return jsonify({"errorMessage": "couldent connect to the users server."})


@app.route('/upload', methods=["POST"])
def upload():
    print(request.data.decode())
    fileVisibility = json.loads(request.data.decode())[
        "rank"]  # Getting the visibility from the request we got from the js
    pathToFile = json.loads(request.data.decode())["file"]
    fileSize = 1
    fileName = 1
    """
    If the file size is 1MB or less the piece size will be 500KB
    If the file size is 10MB or less the piece size will be 1MB
    If the file size is 100MB or less the piece size will be 2MB
    If the file size is 1GB or less the piece size will be 5MB
    """
    if 0 <= fileSize <= 1000000:
        pieceSize = 50000
    elif 1000000 < fileSize <= 10000000:
        pieceSize = 1000000
    elif 10000000 < fileSize <= 100000000:
        pieceSize = 2000000
    elif 100000000 < fileSize <= 1000000000:
        pieceSize = 5000000
    else:
        # TODO: tell the user that you cant upload a file bigger then 1GB and cancel the submit file.
        return jsonify({"errorMessage": "Cant upload a file bigger then 1GB."})
    amountOfPieces = math.ceil(fileSize / pieceSize)
    fileOwner = socket.gethostbyname(socket.gethostname())
    peerList = [fileOwner]
    fileOwners = json.dumps({"Peers": peerList})
    fileUploader = json.dumps(flask_login.current_user.__dict__)
    # Initialize an empty list to store piece hashes
    hashes_list = []

    with open(pathToFile, 'rb') as file:  # Code from gpt
        file_content = file.read()

        for i in range(amountOfPieces):
            start_idx = i * pieceSize
            end_idx = (i + 1) * pieceSize
            pieceData = file_content[start_idx:end_idx] if i != amountOfPieces - 1 else file_content[start_idx:]
            hashObject = hashlib.sha256()
            hashObject.update(pieceData)
            pieceHash = hashObject.hexdigest()
            hashes_list.append(pieceHash)

    hashes_list = json.dumps({
        "hashes": hashes_list
    })

    # Connect to the tracker and send him the new file
    requestStatus = TrackerRequest.upload_file_to_tracker(flask_login.current_user.__dict__["tracker"],
                                                          flask_login.current_user.__dict__, fileName,
                                                          fileSize, pieceSize, amountOfPieces, fileVisibility,
                                                          fileOwners, fileUploader, hashes_list)

    return jsonify(requestStatus)


@app.route('/download', methods=["POST"])
def download():
    data = request.data.decode()
    fileData = json.loads(data)["fileInfo"]
    downloadStatus = download_file(flask_login.current_user.__dict__["tracker"], fileData["fileID"],
                                   fileData["fileName"],
                                   int(fileData["numOfPieces"]), int(fileData["pieceSize"]))

    return jsonify(downloadStatus)


@app.route('/refresh', methods=["POST"])
def refresh():
    return redirect("/application")  # That simple?


@app.route("/delete", methods=["POST"])
def delete():
    data = request.data.decode()
    fileData = json.loads(data)["fileInfo"]
    deleteStatus = TrackerRequest.delete_file(flask_login.current_user.__dict__["tracker"],
                                              flask_login.current_user.__dict__, fileData["fileID"],
                                              fileData["fileName"])

    return jsonify(deleteStatus)


def download_file(tracker, fileID, fileName, amountOfPieces, pieceSize):
    dataFromTracker = TrackerRequest.start_download(tracker, flask_login.current_user.__dict__, fileID, fileName)
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
        for piece in range(
                amountOfPieces):
            with open("{}/{}{}".format(filesFolder, piece, fileName), "rb") as pieceFile:
                pieceData = pieceFile.read()
            fileData += pieceData
            os.remove("{}/{}{}".format(filesFolder, piece, fileName))

        with open("{}/{}".format(filesFolder, fileName), "wb") as file:
            file.write(fileData)

        return {"status": "The download went well."}
    except KeyError:  # This error means we didn't get the peers and hashes from the tracker,
        # but instead we got a error message
        # TODO: notify the user we couldn't connect to the tracker.
        return {
            "errorMessage": "coldest connect to the tracker you provided. please try again or check if the tracker is still active"}
    except Exception:  # General exception just in case
        return {"errorMessage": "couldn't download the file."}


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


if __name__ == "__main__":
    pServer = PeerServer()
    threading.Thread(target=pServer.start_peer_server).start()
    app.run(host="0.0.0.0", port=80)
