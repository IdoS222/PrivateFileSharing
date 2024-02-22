import base64
import hashlib
import json
import socket
import threading
import flask
import flask_login
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect
import os
import subprocess
from UserFunctions import UserFunctions
from user import User


userActive = {}
app = Flask(__name__, template_folder=os.path.join("www", "templates"),static_folder=os.path.join("www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)
# login_manager.login_view = "/"  # will redirect user to login page

filesFolder = r"C:\Users\owner\Desktop\Test2"

# todo: custom decorator for specific usage (@admin_required)
# todo:


@app.route('/')
# @flask_login.login_required
def index():
    if flask_login.current_user.is_authenticated:
        return render_template("index.html")

    return redirect("/login")

    if request.method == "GET":
        try:  # We are trying to connect to the tracker to get all the files before giving the page back to the user.
            return render_template("index.html")

            """
            # Connecting to the tracker and getting the announcing info and the files
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(tuple(tracker))
            announcingRequest = {
                "requestType": 6,
                "userID": user.user_id,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "email": user.email,
                "rank": user.rank
            }
            sock.send(json.dumps(announcingRequest).encode())
            announcingInfo = json.loads(sock.recv(1024))
            try:
                print(announcingInfo["trackerName"])
                print(announcingInfo["trackerDescription"])
                print(announcingInfo["trackerOwner"])
            except Exception:
                # we didn't get the announcing info from the tracker.
                return render_template("index.html")

            filesRequest = {
                "requestType": 0,
                "userID": user.user_id,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "email": user.email,
                "rank": user.rank
            }
            sock.send(json.dumps(filesRequest).encode())
            files = json.loads(sock.recv(1024))

            print(files)

            return render_template("index.html", files=files)
        """
        except Exception as e:
            print(e)


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
    except Exception:
        # In this case, the values we wanted didn't arrive, and we need to do something about it (they think they are tough, we are tougher)
        return render_template("tough_guy.html")

    # Trying to register the user in the database after verifying the values we got.
    answer = UserFunctions.register_new_user(request.values["firstName"], request.values["lastName"],
                                             request.values["email"], request.values["password"],
                                             request.values["confirmPassword"], "visitor")

    if answer == "Successfully register the user {} to the database.".format(request.values["email"]):
        # If we got here, we successfully registered the user, so we can tell the user that and redirect him to the login page
        return redirect('/login')
    else:
        return answer


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    try:
        print(request.values["email"])
        print(request.values["password"])
    except Exception:
        return render_template("tough_guy.html")

    answer = UserFunctions.process_login(request.values["email"], request.values["password"])
    if answer == "Successful login.":
        info = UserFunctions.get_user_info(request.values["email"])
        userActive[flask.request.values["email"]] = User(info[0], info[1], info[2], info[3], info[4],
                                                         ["0.0.0.0", 6987])
        flask_login.login_user(userActive.get(flask.request.values["email"]))
        return redirect('/')
    else:
        return answer


#


@login_manager.user_loader
def load_user(user_email):
    # Serch user email in db
    #found_user = users.find_one(user_email)
    #if found_user:
        #return User()  # create instance of User

    return None
    # return userActive.get(user_email)


@login_manager.unauthorized_handler
def unauthorized_callback():  # This handler is called when trying to acsess the index page without a login session.
    return redirect('/login')


@app.route("/logout")
def logout():  # handling the logout
    userActive.popitem()
    flask_login.logout_user()
    return redirect("/login")


@app.route("/settings", methods=["GET", "POST"])
@flask_login.login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")


def download_file(fileID, fileName, fileSize, pieceSize, amountOfPieces, path):
    """
    Downloading a file.
    :param fileID: The id of the file in the database.
    :param fileName: The name of the file.
    :param fileSize: The size of the file.
    :param pieceSize: The size of one piece.
    :param amountOfPieces: The number of pieces needed to create a file.
    :param path: Where to download the file to.
    :return: True if the download succeeded and false if it isn't.
    """

    # Sending another request to the tracker incase the amount of owners is different and to get the list of hashes
    user = list(userActive.values())[0]
    request = json.dumps({
        "requestType": 2,
        "userID": user.user_id,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "email": user.email,
        "rank": user.rank,
        "fileID": fileID,
        "fileName": fileName
    })

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(tuple(user.tracker))
    sock.send(request.encode())

    dataFromTracker = sock.recv(1024).decode()
    jsonData = json.loads(dataFromTracker)

    listOfHashes = jsonData["listOfHashes"]
    fileOwners = jsonData["Peers"]
    pieces = []

    for piece in range(amountOfPieces):
        pieces.append(piece)

    # Distribution of the pieces between owners
    piecesPerOwner = len(pieces) // len(fileOwners)
    remainingPieces = len(pieces) % len(fileOwners)

    distribution = {owner: [] for owner in fileOwners}

    threads = []
    pieceIndex = 0
    for owner in fileOwners:
        # Distribute equal pieces to each owner
        thread_pieces_indices = list(range(pieceIndex, pieceIndex + piecesPerOwner))
        t = threading.Thread(target=download_pieces_from_peer,
                             args=(owner, thread_pieces_indices, pieceSize, fileName, path, listOfHashes))
        t.start()
        threads.append(t)
        distribution[owner].extend(thread_pieces_indices)
        pieceIndex += piecesPerOwner

        # Distribute remaining pieces if any
        if remainingPieces > 0:
            remaining_piece_index = pieceIndex
            t = threading.Thread(target=download_pieces_from_peer,
                                 args=(owner, [remaining_piece_index], pieces, pieceSize, fileName, path, listOfHashes))
            t.start()
            threads.append(t)
            distribution[owner].append(remaining_piece_index)
            pieceIndex += 1
            remainingPieces -= 1

    for thread in threads:
        thread.join()

    fileData = b''
    # Merge all the small files to one large file.
    for piece in range(amountOfPieces):
        with open("{}/{}{}".format(path, piece, fileName), "rb") as pieceFile:
            pieceData = pieceFile.read()
        fileData += pieceData
        os.remove("{}/{}{}".format(path, piece, fileName))

    with open("{}/{}".format(path, fileName), "wb") as file:
        file.write(fileData)

    # Validate the file size.


def download_pieces_from_peer(addr, piecesToDownload, pieceSize, fileName, path, listOfHashes):
    """
    Downloading all the pieces the function is instructed to from the peer on the addr.
    :param path: Where to download the file
    :param addr: The address of the peer.
    :param piecesToDownload: The pieces we need to download
    :param pieceSize: The size of each piece.
    :param fileName: The name of the file.
    :param listOfHashes: A list of hashes for each piece.
    :return: Nothing.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(tuple(addr))
    for piece in piecesToDownload:
        pieceRequest = {
            "requestType": "downloadPart",
            "pieceNumber": piece,
            "pieceSize": pieceSize,
            "fileName": fileName
        }
        sock.send(json.dumps(pieceRequest).encode())
        buffer = ""
        lenOfData = ""
        while buffer != ".":
            buffer = sock.recv(1).decode()
            lenOfData += buffer
        dataFromPeer = sock.recv(int(lenOfData[:-1])).decode()
        jsonData = json.loads(dataFromPeer)
        chuckData = base64.b64decode(jsonData["data"])
        # Validate the piece
        chuckHash = hashlib.sha256(chuckData)
        if chuckHash != listOfHashes[piece]:
            print("we got a broken piece. index:{}".format(piece))
            continue
        with open("{}/{}{}".format(path, piece, fileName), "wb") as file:
            subprocess.run(["attrib", "+H", "{}/{}{}".format(path, piece, fileName)], check=True)
            file.write(chuckData)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
