import re
import socket
import sqlite3
import os
import random
import string
import threading
import json
import hashlib
from SocketFunctions import SocketFunctions


class UsersServer:
    def __init__(self, databaseLocation):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MAX_CONNECTIONS = 1500
        self.serverAlive = False
        self.databaseLocation = databaseLocation

    def start_users_server(self):
        """
        Start the server and start waiting for connection
        :return: Nothing
        """
        self.create_database()
        try:
            self.serverSocket.bind(("0.0.0.0", 29574))
            self.serverSocket.listen(self.MAX_CONNECTIONS)
            self.serverAlive = True
            while self.serverAlive:
                clientSocket, addr = self.serverSocket.accept()
                print("new connection is made with {}".format(addr))
                threading.Thread(target=self.server_loop, args=[clientSocket, ]).start()
        except Exception as e:
            self.serverAlive = False
            print("Couldn't start the server. " + str(e))

    def server_loop(self, clientSocket):
        """
        The loop that will occur in a thread when a new connection is made with a client.
        :param clientSocket: The socket that the server automatically creates when a new connection is made.
        :return: Nothing
        """
        peerInterested = True
        while peerInterested:
            try:
                data = SocketFunctions.read_from_socket(clientSocket)
                if data:
                    dataFromPeer = json.loads(data)
                    match dataFromPeer["requestType"]:
                        case "registerUser":
                            status = self.register_new_user(dataFromPeer["firstName"], dataFromPeer["lastName"],
                                                            dataFromPeer["email"], dataFromPeer["password"],
                                                            dataFromPeer["confirmPassword"], dataFromPeer["rank"])
                            SocketFunctions.send_data(clientSocket, status)
                        case "processLogin":
                            status = self.process_login(dataFromPeer["email"], dataFromPeer["password"])

                            SocketFunctions.send_data(clientSocket, status)
                        case "userExist":
                            status = self.user_exists(dataFromPeer["userID"], dataFromPeer["firstName"],
                                                      dataFromPeer["lastName"], dataFromPeer["email"],
                                                      dataFromPeer["rank"])
                            SocketFunctions.send_data(clientSocket, status)
                        case "removeUser":
                            # TODO: secure this shit before processing the request.
                            status = self.remove_user(dataFromPeer["email"])
                            SocketFunctions.send_data(clientSocket, status)
                        case "getUserInfo":
                            status = self.get_user_info(dataFromPeer["email"])
                            SocketFunctions.send_data(clientSocket, status)
                        case "changeTracker":
                            status = self.change_tracker(dataFromPeer["email"], dataFromPeer["tracker"])
                            SocketFunctions.send_data(clientSocket, status)
                else:
                    continue
            except KeyError as e:
                # This means that we got an illegal request.
                print(e)
                SocketFunctions.send_data(clientSocket, (json.dumps({"errorMessage": "Couldn't send the data"})))
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

    def register_new_user(self, firstName, lastName, email, password, confirmPassword, rank):
        """
        Adding a new user to the database if the user doesn't exist and if all the fields check out.
        :param firstName: The first name of the user.
        :param lastName: The last name of the user.
        :param email: The email of the user.
        :param password: The password of the user.
        :param confirmPassword: Confirming the password.
        :param rank: The rank of the user.
        :return: The error message if the register failed and the success otherwise.
        """
        # Checking the values from the client
        if len(firstName) <= 2:
            return json.dumps({"status": "The first name is too short."})
        if len(lastName) <= 2:
            return json.dumps({"status": "The last name if too short."})
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return json.dumps({"status": "The email is illegal."})
        if len(password) <= 5:
            return json.dumps({"status": "The password is too short"})
        if password != confirmPassword:
            return json.dumps({"status": "The password and the confirm password dont match"})

        # Hash the password using SHA-256 from hashlib
        salt = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=32))
        passHash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        try:  # registering the user in the database
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers:  # if it goes into this condition, it means the list is empty and there is no user with this email, and we can proceed with adding the user to the database
                command = "INSERT INTO users (firstName, lastName, email, passHash, rank, salt, tracker) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    firstName, lastName, email, passHash, rank, salt, "No")
                usersCurser.execute(command)
                usersConnection.commit()
                usersConnection.close()
                return json.dumps({"status": "Successfully register the user {} to the database.".format(email)})
            else:
                return json.dumps(
                    {"errorMessage": "There is a user with this email. please change the email or log in."})
        except Exception as e:
            return json.dumps({
                "errorMessage": "Couldn't add the user {} from the database. Here is the error log: {}".format(
                    firstName, str(e))})

    def process_login(self, email, password):
        """
        Process the login request from the user
        :param email: The email of the user
        :param password: The password of the user
        :return: True if the login is successful and false if it isn't
        """

        # Hash the password using SHA-256 from hashlib
        try:
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search

            if not existingUsers or len(existingUsers) > 1:
                return json.dumps({"errorMessage": "The user doesnt exists"})
            else:
                try:
                    hashed_password = hashlib.sha256((password + existingUsers[0][6]).encode('utf-8')).hexdigest()
                    if existingUsers[0][4] != hashed_password:
                        return json.dumps({"errorMessage": "The password is wrong."})
                    else:
                        return json.dumps({"status": "Successful login."})
                except Exception:
                    return json.dumps({"errorMessage": "The password is wrong."})
        except Exception as e:
            return json.dumps({"errorMessage": "Couldn't validate the login request."})

    def user_exists(self, userID, firstName, lastName, email, rank):
        """
        Checks if the user exists in the database.
        :param userID: The user id of the user.
        :param firstName: The first name of the user.
        :param lastName: The last name of the user.
        :param email: The email of the user.
        :param rank: The rank of the user.
        :return: True if the user exists and false if it isn't.
        """
        try:
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers:
                return json.dumps({"status": "The user doesnt exists"})
            else:
                if len(existingUsers) > 1:
                    return json.dumps({"status": "The user doesnt exists"})
                else:
                    if existingUsers[0][0] == userID and existingUsers[0][1] == firstName and existingUsers[0][2] == lastName and existingUsers[0][3] == email and existingUsers[0][5] == rank:
                        return json.dumps({"status": "The user exists"})
                    else:
                        return json.dumps({"status": "The user doesnt exists"})
        except Exception as e:
            return json.dumps({"errorMessage": "couldn't check if the user exists " + str(e)})

    def remove_user(self, email):
        """
        Removes a user from the database.
        :param email: The email of the user.
        :return: The status of the request.
        """
        try:
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return json.dumps({
                    "status": "There is no user in the database with the email {} or there is more then one user with this email.".format(
                        email)})
            else:
                usersCurser.execute("DELETE FROM users WHERE email = '{}'".format(email))
                usersConnection.commit()
                usersConnection.close()
                return json.dumps({"status": "Successfully removed user {} from the database".format(email)})
        except Exception as e:
            return json.dumps({"errorMessage": "Couldn't remove the user from the database" + str(e)})

    def get_user_info(self, email):
        """
        Getting the user firstname, lastname, email and rank.
        :param email: The email of the user.
        :return: A list of the user information.
        """
        try:
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return json.dumps({"errorMessage": "The user doesnt exists"})
            else:
                user = list(existingUsers[0])
                del user[4]
                del user[5]
                return json.dumps({"status": user})

        except Exception as e:
            return json.dumps({"errorMessage": "couldn't check if the user exists " + str(e)})

    def change_tracker(self, email, tracker):
        """
        Changing the current tracker in the database
        :param email: The email of the user.
        :param tracker: The tracker we want to change to.
        :return: The status of the request.
        """

        try:
            usersConnection = sqlite3.connect(self.databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return json.dumps({"status": "The user doesnt exists"})
            else:
                usersCurser.execute("UPDATE users SET tracker = '{}' WHERE email = '{}'".format(tracker, email))
                usersConnection.commit()
                usersConnection.close()
                return json.dumps({"status": "tracker set"})
        except Exception as e:
            return json.dumps({"errorMessage": "couldn't check if the user exists " + str(e)})

    def create_database(self):
        """
        Create a new database if there isn't a one.
        :return: Nothing
        """
        # checking if the databases exist
        if not os.path.isfile(self.databaseLocation):  # Checking if the file's database exists.
            try:
                open(self.databaseLocation, "x")
                usersConnection = sqlite3.connect(self.databaseLocation)
                usersCurser = usersConnection.cursor()

                usersCurser.execute("""CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        firstName TEXT,
                        lastName TEXT,
                        email TEXT,
                        passHash TEXT,
                        rank TEXT,
                        salt TEXT,
                        tracker TEXT
                )""")

                usersConnection.commit()
                usersConnection.close()
                print("The database is created. please restart the server.")
                exit()
            except Exception as e:
                print("There was an error trying to create the database. The error is: {}".format(str(e)))
                exit()


u = UsersServer(r"C:\Users\Owner\Desktop\עידו\school\הנדסת תוכנה\PrivateFileSharing\usersServer\users.db")
u.start_users_server()
