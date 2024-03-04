import base64
import json
import socket
import threading
import hashlib
from tkinter import filedialog
import flask_login
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect
import os
import subprocess
from User import User
from TrackerRequests import TrackerRequest
from PeerServer import PeerServer
import concurrent.futures
import ipaddress
from SocketFunctions import SocketFunctions
from tkinter import Tk

app = Flask(__name__, template_folder=os.path.join("www", "templates"),
            static_folder=os.path.join("www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)
login_manager.session_protection = "strong"
filesFolder = r"C:\Users\owner\Desktop\Test2"
usersServerLocation = ("127.0.0.1", 29574)
activeUser = None


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/application', methods=['GET', 'POST'])
@flask_login.login_required
def application():
    if request.method == "GET":
        if flask_login.current_user.__dict__["tracker"] != "No":
            try:
                print(tuple(flask_login.current_user.__dict__["tracker"]))
                trackerData = TrackerRequest.get_tracker_data(tuple(flask_login.current_user.__dict__["tracker"]),
                                                              flask_login.current_user.__dict__)
                filesFromTracker = TrackerRequest.get_files_from_tracker(
                    tuple(flask_login.current_user.__dict__["tracker"]),
                    flask_login.current_user.__dict__)
                return render_template("application.html", files=filesFromTracker, trackerData=trackerData)
            except ConnectionRefusedError:
                # Send the application template with a message that we couldn't connect to the tracker.
                return render_template("application.html")
        else:
            return render_template("application.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")

    try:  # trying to see if all the values we expected arrived.
        print(request.values["firstName"])
        print(request.values["lastName"])
        print(request.values["email"])
        print(request.values["password"])
        print(request.values["confirmPassword"])
    except KeyError:
        # In this case, the values we wanted didn't arrive, and we need to do something about it (they think they are
        # tough, we are tougher)
        return render_template("tough_guy.html")

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
    try:
        if jsonStatus["status"] == "Successfully register the user {} to the database.".format(request.values["email"]):
            return redirect('/application')
    except KeyError:  # If we get in here we got an error message from the server and the registration failed
        return jsonStatus["errorMessage"]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # Validating the login request we got.
    try:
        print(request.values["email"])
        print(request.values["password"])
    except KeyError:
        return render_template("tough_guy.html")
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

        try:
            if loginJsonStatus["status"] == "Successful login.":
                try:
                    if userInfoStatus["status"] != "The user doesnt exists":
                        # If we got here we also got the info from the server, and we can finally log in
                        user = userInfoStatus["status"]  # The list of all the user info
                        # Update the active tracker
                        tracker = "No"
                        if user[5] != "No":
                            trackerDict = json.loads(user[5])
                            tracker = [trackerDict["ip"], trackerDict["port"]]
                        flask_login.login_user(User(user[0], user[1], user[2], user[3], user[4], tracker),
                                               remember=True)
                        return redirect('/application')
                    else:
                        # if we got here we didn't get the user info, but the user probably doesn't exist
                        return "The user doesnt exists"
                except KeyError:
                    # If we got here, we got an error message from the get user info request.
                    return userInfoStatus["errorMessage"]
        except KeyError:  # If we get in here we got an error message from the server and the login failed
            return loginJsonStatus["errorMessage"]
    except Exception:  # If we got here we couldn't connect or get the data from the server
        return "couldn't connect to the server"


@login_manager.user_loader
def load_user(user_email):
    # Search user email in db
    userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    userSocket.connect(usersServerLocation)
    SocketFunctions.send_data(userSocket, json.dumps({  # This is the request for registering a new user
        "requestType": "getUserInfo",
        "email": user_email,
    }))

    data = SocketFunctions.read_from_socket(userSocket)
    jsonStatus = json.loads(data)
    try:
        if jsonStatus["status"] == "The user doesnt exists":
            return None  # The user doesn't exist, and we need to send None

        found_user = jsonStatus["status"]
        if found_user[5] == "No":
            return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],
                        "No")
        tracker = json.loads(found_user[5])
        return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],
                    (tracker["ip"], tracker["port"]))
    except KeyError:  # we got an error message from the server
        return None


@login_manager.unauthorized_handler
def unauthorized_callback():  # This handler is called when trying to access the application page without a login
    # session.
    return redirect('/login')


@app.route("/logout")
def logout():  # handling the logout
    if request.method != "POST":
        # We don't want to get a get request for here.
        return redirect("/login")

    flask_login.logout_user()
    return redirect("/login")


@app.route("/settings", methods=["GET", "POST"])
@flask_login.login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")

    try:
        print(request.values["ipAddress"])
    except KeyError:
        return render_template("tough_guy.html")

    # Checking the values of the tracker change request.
    try:
        ipObj = ipaddress.ip_address(request.values["ipAddress"])
        # If we got here without an exception thrown, the ip address is valid
    except ValueError:
        # The ip given is not an ip address.
        print("Ip address isn't valid.")
        return redirect("application.html")

    usersSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    usersSocket.connect(usersServerLocation)

    SocketFunctions.send_data(usersSocket.send, json.dumps({
        "requestType": "changeTracker",
        "email": flask_login.current_user.__dict__["email"],
        "tracker": json.dumps({"ip": request.values["ipAddress"], "port": 6987})
    }))

    data = SocketFunctions.read_from_socket(usersSocket)
    jsonData = json.loads(data)

    try:
        if jsonData["status"] == "tracker set":
            activeTracker = [(request.values["ipAddress"], int(request.values["port"]))]
            flask_login.current_user.__dict__["tracker"] = activeTracker
            print(flask_login.current_user.__dict__["tracker"])
            return redirect("/application")
        else:
            # problem setting the tracker
            print(jsonData)
    except KeyError:
        # error while setting the tracker
        print(jsonData)

    return render_template("tough_guy.html")


@app.route('/upload', methods=["POST"])
def upload():
    if request.method != "POST":
        # We don't want to get a get request for here.
        return redirect("/login")

    root = Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)
    pathToFile = filedialog.askopenfilename(title="Select a file to upload to the tracker.")
    fileName = os.path.basename(pathToFile)
    fileSize = os.stat(pathToFile).st_size
    if fileSize < 10000:  # If the file is less than 10 KB,
        # there is no reason to split it into the standard 1000 pieces,
        # and we will split it into 10 pieces 1KB each
        amountOfPieces = 10
    else:
        amountOfPieces = 1000
    pieceSize = fileSize / amountOfPieces
    fileVisibility = "visitor"  # TODO: Change that to ask the user.
    fileOwner = [socket.gethostbyname(socket.gethostname()), 15674]
    fileOwners = json.dumps({"Peers": list(fileOwner)})
    fileUploader = json.dumps(flask_login.current_user.__dict__)

    # Connect to the tracker and send him the new file
    requestStatus = TrackerRequest.upload_file_to_tracker(flask_login.current_user.__dict__["tracker"],
                                                          flask_login.current_user.__dict__, fileName,
                                                          fileSize, pieceSize, amountOfPieces, fileVisibility,
                                                          fileOwners, fileUploader)
    try:
        if requestStatus["status"] == "success":
            # Notify the user that the upload went smoothly.
            return redirect("/application")

        # Notify that something went wrong
        return redirect("/application")
    except KeyError:
        # Notify that something went wrong
        return redirect("/application")


@app.route('/refresh', methods=["POST"])
def refresh():
    if request.method != "POST":
        # We don't want to get a get request for here.
        return redirect("/login")

    return redirect("/application")  # That simple?


def download(tracker, numPieces, pieceSize, fileName, fileID):
    """
    Downloading a file from the peers.
    :param fileID: The id of the file.
    :param tracker: The tracker we are downloading the file from.
    :param numPieces: The number of pieces that make up the file.
    :param pieceSize: The size of each piece.
    :param fileName: The name of the file.
    :return: Nothing
    """

    def find_another_peer(current_peer):
        """
        Find another peer to download the piece from.
        :param current_peer: The current peer.
        :return: Another peer.
        """
        return next(peer for peer in peerList if peer != current_peer)

    dataFromTracker = TrackerRequest.start_download(tracker, flask_login.current_user.__dict__, fileID, fileName)
    peerList = dataFromTracker["Peers"]
    hashList = dataFromTracker["listOfHashes"]

    piecesPerPeer = numPieces // len(peerList)
    remainingPieces = numPieces % len(peerList)

    with concurrent.futures.ThreadPoolExecutor():
        for i, peer in enumerate(peerList):
            startPiece = i * piecesPerPeer + min(i, remainingPieces)
            endPiece = startPiece + piecesPerPeer + (1 if i < remainingPieces else 0)

            for pieceIndex in range(startPiece, endPiece):
                success = download_piece_from_peer(peer, pieceIndex, pieceSize, fileName, filesFolder, hashList)

                while not success:
                    retryPeer = find_another_peer(peer)
                    if retryPeer:
                        success = download_piece_from_peer(retryPeer, pieceIndex, pieceSize, fileName, filesFolder,
                                                           hashList)
                    else:
                        pass
    # The process of merging all the files.
    fileData = b''
    # Merge all the small files to one large file.
    for piece in range(numPieces):
        with open("{}/{}{}".format(filesFolder, piece, fileName), "rb") as pieceFile:
            pieceData = pieceFile.read()
        fileData += pieceData
        os.remove("{}/{}{}".format(filesFolder, piece, fileName))

    with open("{}/{}".format(filesFolder, fileName), "wb") as file:
        file.write(fileData)


def download_piece_from_peer(addr, piece, pieceSize, fileName, path, hashlist):
    """
    Downloading the piece, the function is instructed to from the peer on the addr.
    :param path: Where to download the file to.
    :param addr: The address of the peer.
    :param piece: The piece we need to download
    :param pieceSize: The size of each piece.
    :param fileName: The name of the file.
    :return: True if the piece is downloaded and verified and false if it isn't.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(tuple(addr))
    pieceRequest = {
        "requestType": "downloadPart",
        "pieceNumber": piece,
        "pieceSize": pieceSize,
        "fileName": fileName
    }
    SocketFunctions.send_data(sock, json.dumps(pieceRequest))
    dataFromPeer = SocketFunctions.read_from_socket(sock)
    jsonData = json.loads(dataFromPeer)
    chuckData = base64.b64decode(jsonData["data"])
    # Validate the piece
    chuckHash = hashlib.sha256(chuckData).hexdigest()
    if chuckHash != hashlist[piece]:
        # We didn't get the correct data from the piece, and we need to download it from another peer.
        return False
    with open("{}/{}{}".format(path, piece, fileName), "wb") as file:
        subprocess.run(["attrib", "+H", "{}/{}{}".format(path, piece, fileName)], check=True)
        file.write(chuckData)

    return True


if __name__ == "__main__":
    pServer = PeerServer()
    threading.Thread(target=pServer.start_peer_server).start()
    app.run(host="0.0.0.0", port=80)
