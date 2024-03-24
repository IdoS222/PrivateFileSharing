import base64
import json
import socket
import hashlib
from tkinter import filedialog
import flask_login
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect, jsonify
import os
import subprocess
from User import User
from TrackerRequests import TrackerRequest
import ipaddress
from SocketFunctions import SocketFunctions
from tkinter import Tk
import math
from DBFunctions import DBFunctions

app = Flask(__name__, template_folder=os.path.join("../client/www", "templates"),
            static_folder=os.path.join("../client/www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)
login_manager.session_protection = "strong"
databaseLocation = r"C:\Users\Owner\Desktop\עידו\school\הנדסת תוכנה\PrivateFileSharing\users.db"


@app.route('/')
def index():
    # TODO: MAKE A INDEX PAGE
    return render_template("index.html")


@app.route('/userExists', methods=['GET'])
def userExists():
    userID = request.args.get("userID")
    if userID is None:
        return "please provide a user id with the request"
    email = request.args.get("email")
    if email is None:
        return "please provide an email with the request"
    firstName = request.args.get("firstName")
    if firstName is None:
        return "please provide a first name with the request"
    lastName = request.args.get("lastName")
    if lastName is None:
        return "please provide a last name with the request"
    rank = request.args.get("rank")
    if rank is None:
        return "please provide a rank with the request"

    userExists = DBFunctions.user_exists(userID, firstName, lastName, email, rank, databaseLocation)
    if "status" in userExists.keys():
        # Means the user exists
        return "True"
    else:
        return "False"


@app.route('/application', methods=['GET', 'POST'])
@flask_login.login_required
def application():
    if request.method == "GET":
        if flask_login.current_user.__dict__["tracker"] != "No":
            trackerInfoAndFiles = TrackerRequest.get_files_and_tracker_info_from_tracker(
                flask_login.current_user.__dict__["tracker"], flask_login.current_user.__dict__)
            print(trackerInfoAndFiles)
            if len(trackerInfoAndFiles) == 1:
                # The only reason this list is of len 1 is that we got an error message.
                return render_template("application.html", errorMessage=trackerInfoAndFiles[0]["errorMessage"])

            return render_template("application.html", files=trackerInfoAndFiles[0],
                                   trackerInfo=trackerInfoAndFiles[1])
        else:
            # There is no active tracker and we need to notify the user.
            return render_template("application.html",
                                   errorMessage="There is no active tracker! please connect to a tracker from the settings page.")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")

    try:  # trying to see if all the values we expected arrived.
        # x is a temp value top check if we get a KeyError.
        x = request.values["firstName"]
        x = request.values["lastName"]
        x = request.values["email"]
        x = request.values["password"]
        x = request.values["confirmPassword"]
    except KeyError:
        # In this case, the values we wanted didn't arrive, and we need to do something about it (they think they are tough, we are tougher)
        return render_template("tough_guy.html")

    # Trying to register the user in the database after verifying the values we got.
    status = DBFunctions.register_new_user(request.values["firstName"], request.values["lastName"],
                                           request.values["email"],
                                           request.values["password"], request.values["confirmPassword"], "visitor",
                                           databaseLocation)

    return jsonify(status)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # Validating the login request we got.
    try:
        # x is a temp value top check if we get a KeyError.
        x = request.values["email"]
        x = request.values["password"]
    except KeyError:
        return render_template("tough_guy.html")

    loginStatus = DBFunctions.process_login(request.values["email"], request.values["password"], databaseLocation)

    if "status" in loginStatus.keys():
        # If we got a status key, the login went smoothly. And we can check for the tracker in the user info
        infoStatus = DBFunctions.get_user_info(request.values["email"], databaseLocation)
        if "status" in infoStatus.keys():
            # we also got the user info without any error, and we can finally log into the system
            user = infoStatus["status"]  # The list of all the user info
            # Update the active tracker
            tracker = "No"
            if user[5] != "No":
                trackerDict = json.loads(user[5])
                tracker = [trackerDict["ip"], trackerDict["port"]]
            flask_login.login_user(User(user[0], user[1], user[2], user[3], user[4], tracker), remember=True)
            return redirect('/application')
        else:
            return jsonify(infoStatus["errorMessage"])
    else:
        return jsonify(loginStatus["errorMessage"])


@login_manager.user_loader
def load_user(userEmail):
    # Search user email in db
    status = DBFunctions.get_user_info(userEmail, databaseLocation)
    if "status" in status.keys():
        # everything went well, and we didn't get any error.
        found_user = status["status"]
        if found_user[5] == "No":  # Checking if there are any trackers that the user is connected to and sending it with the user info if yes
            return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],"No")
        tracker = json.loads(found_user[5])
        return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4],
                    (tracker["ip"], tracker["port"]))
    else:
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
        x = request.values["ipAddress"]
        # Checking the values of the tracker change request.
        ipObj = ipaddress.ip_address(request.values["ipAddress"])
    except KeyError:
        return render_template("tough_guy.html")
    except ValueError:
        # The ip given is not an ip address.
        print("Ip address isn't valid.")
        return redirect("application.html")

    status = DBFunctions.change_tracker(flask_login.current_user.__dict__["email"],
                                        {"ip": request.values["ipAddress"], "port": 6987}, databaseLocation)
    return jsonify(status)


@app.route('/upload', methods=["POST"])
def upload():
    if request.method != "POST":
        # We don't want to get a get request for here.
        return redirect("/login")

    root = Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)
    pathToFile = filedialog.askopenfilename(
        title="Select a file to upload to the tracker.")  # TODO: FIGURE OUT WHY THIS FUCKING FILE DIALOG IS NOT FUCKING STABLE FUCK YOU TKINTER FUCKING DOGSHIT
    if pathToFile == '':
        # TODO: tell the user that he canceled the file upload. (maybe not???)
        return redirect('/application')
    fileName = os.path.basename(pathToFile)
    root.destroy()
    fileSize = os.stat(pathToFile).st_size
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
        return redirect("/application")
    amountOfPieces = math.ceil(fileSize / pieceSize)
    fileVisibility = json.loads(request.data.decode())[
        "rank"]  # Getting the visibility from the request we got from the js
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
    try:
        if requestStatus["status"] == "success":
            # TODO: Notify the user that the upload went smoothly.
            return redirect("/application")

        # TODO: Notify that something went wrong
        print(requestStatus["status"])
        return redirect("/application")
    except KeyError:
        # TODO: Notify that something went wrong
        print(requestStatus)
        return redirect("/application")


@app.route('/refresh', methods=["POST"])
def refresh():
    if request.method != "POST":
        # We don't want to get a get request for here.
        return redirect("/login")

    return redirect("/application")  # That simple?


@app.route("/delete", methods=["POST"])
def delete():
    data = request.data.decode()
    fileData = json.loads(data)["fileInfo"]
    deleteStatus = TrackerRequest.delete_file(flask_login.current_user.__dict__["tracker"],
                                              flask_login.current_user.__dict__,
                                              fileData["fileID"], fileData["fileName"])

    return jsonify(
        deleteStatus)  # returning the status so the javascript can handle it and display the message to the user.


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
