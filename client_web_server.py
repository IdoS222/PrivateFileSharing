import base64
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
from User import User
from TrackerRequests import TrackerRequest

app = Flask(__name__, template_folder=os.path.join("www", "templates"),
            static_folder=os.path.join("www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)
login_manager.session_protection = "strong"
filesFolder = r"C:\Users\owner\Desktop\Test2"
activeTracker = []


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/application')
@flask_login.login_required
def application():
    return render_template("application.html", files=[{"name": "naga", "size": 123}, {"name": "nogi", "size": 1234}])


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
        # In this case, the values we wanted didn't arrive, and we need to do something about it (they think they are tough, we are tougher)
        return render_template("tough_guy.html")

    # Trying to register the user in the database after verifying the values we got.
    answer = UserFunctions.register_new_user(request.values["firstName"], request.values["lastName"],
                                             request.values["email"], request.values["password"],
                                             request.values["confirmPassword"], "visitor")

    if answer == "Successfully register the user {} to the database.".format(request.values["email"]):
        flask_login.login_user(load_user(flask.request.values["email"]), remember=True)
        return redirect('/application')
    else:
        # The registration failed
        return answer


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

    answer = UserFunctions.process_login(request.values["email"], request.values["password"])
    if answer == "Successful login.":
        flask_login.login_user(load_user(flask.request.values["email"]), remember=True)
        return redirect('/application')
    else:
        return answer


@login_manager.user_loader
def load_user(user_email):
    # Search user email in db
    found_user = UserFunctions.get_user_info(user_email)
    if found_user == "The user doesnt exists":
        return None  # The user doesn't exist, and we need to send None

    return User(found_user[0], found_user[1], found_user[2], found_user[3], found_user[4])


@login_manager.unauthorized_handler
def unauthorized_callback():  # This handler is called when trying to acsess the application page without a login session.
    return redirect('/login')


@app.route("/logout")
def logout():  # handling the logout
    flask_login.logout_user()
    return redirect("/")


@app.route("/settings", methods=["GET", "POST"])
@flask_login.login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")


def download_file(fileID, fileName, pieceSize, amountOfPieces, path):
    """
    Downloading a file.
    :param fileID: The id of the file in the database.
    :param fileName: The name of the file.
    :param pieceSize: The size of one piece.
    :param amountOfPieces: The number of pieces needed to create a file.
    :param path: Where to download the file to.
    :return: True if the download succeeded and false if it isn't.
    """

    # Sending another request to the tracker incase the amount of owners is different and to get the list of hashes
    fileOwners = TrackerRequest.start_download(activeTracker, flask_login.current_user.__dict__, fileID, fileName)
    pieces = []

    for piece in range(amountOfPieces):
        pieces.append(piece)

    piecesPerOwner = len(pieces) // len(fileOwners)
    remainingPieces = len(pieces) % len(fileOwners)

    distribution = {owner: [] for owner in fileOwners}  # Distribution of the pieces between owners

    threads = []
    pieceIndex = 0
    for owner in fileOwners:
        # Distribute equal pieces to each owner
        thread_pieces_indices = list(range(pieceIndex, pieceIndex + piecesPerOwner))
        t = threading.Thread(target=download_pieces_from_peer,
                             args=(owner, thread_pieces_indices, pieceSize, fileName, path))
        t.start()
        threads.append(t)
        distribution[owner].extend(thread_pieces_indices)
        pieceIndex += piecesPerOwner

        # Distribute remaining pieces if any
        if remainingPieces > 0:
            remaining_piece_index = pieceIndex
            t = threading.Thread(target=download_pieces_from_peer,
                                 args=(owner, [remaining_piece_index], pieces, pieceSize, fileName, path))
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


def download_pieces_from_peer(addr, piecesToDownload, pieceSize, fileName, path):
    """
    Downloading all the pieces the function is instructed to from the peer on the addr.
    :param path: Where to download the file to.
    :param addr: The address of the peer.
    :param piecesToDownload: The pieces we need to download
    :param pieceSize: The size of each piece.
    :param fileName: The name of the file.
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
        """
        chuckHash = hashlib.sha256(chuckData)
        if chuckHash != listOfHashes[piece]:
            # We didn't get the correct data from the piece, and we need to download it from another peer.
            print("we got a broken piece. index:{}".format(piece))
            continue
        """
        with open("{}/{}{}".format(path, piece, fileName), "wb") as file:
            subprocess.run(["attrib", "+H", "{}/{}{}".format(path, piece, fileName)], check=True)
            file.write(chuckData)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
