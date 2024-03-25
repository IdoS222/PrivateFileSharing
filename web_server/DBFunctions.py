import re
import random
import string
import sqlite3
import hashlib
import os


class DBFunctions:
    @staticmethod
    def register_new_user(firstName, lastName, email, password, confirmPassword, rank, databaseLocation):
        """
        Adding a new user to the database if the user doesn't exist and if all the fields check out.
        :param firstName: The first name of the user.
        :param lastName: The last name of the user.
        :param email: The email of the user.
        :param password: The password of the user.
        :param confirmPassword: Confirming the password.
        :param rank: The rank of the user.
        :param databaseLocation: The location of the database.
        :return: The error message if the register failed and the success otherwise.
        """
        # Checking the values from the client
        if len(firstName) <= 2:
            return {"errorMessage": "The first name is too short."}
        if len(lastName) <= 2:
            return {"errorMessage": "The last name if too short."}
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return {"errorMessage": "The email is illegal."}
        if len(password) <= 5:
            return {"errorMessage": "The password is too short"}
        if password != confirmPassword:
            return {"errorMessage": "The password and the confirm password dont match"}

        # Hash the password using SHA-256 from hashlib
        salt = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=32))
        passHash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        try:  # registering the user in the database
            usersConnection = sqlite3.connect(databaseLocation)
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
                return {"status": "Successfully register the user {} to the database.".format(email)}
            else:
                return {"errorMessage": "There is a user with this email. please change the email or log in."}
        except Exception as e:
            return {"errorMessage": "Couldn't add the user {} from the database. Here is the error log: {}".format(firstName, str(e))}

    @staticmethod
    def process_login(email, password, databaseLocation):
        """
        Process the login request from the user
        :param email: The email of the user
        :param password: The password of the user
        :param databaseLocation: The location of the database.
        :return: True if the login is successful and false if it isn't
        """

        # Hash the password using SHA-256 from hashlib
        try:
            usersConnection = sqlite3.connect(databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search

            if not existingUsers or len(existingUsers) > 1:
                return {"errorMessage": "The user doesnt exists"}
            else:
                try:
                    hashed_password = hashlib.sha256((password + existingUsers[0][6]).encode('utf-8')).hexdigest()
                    if existingUsers[0][4] != hashed_password:
                        return {"errorMessage": "The password is wrong."}
                    else:
                        return {"status": "Successful login."}
                except Exception:
                    return {"errorMessage": "The password is wrong."}
        except Exception as e:
            print("Couldn't validate the login request. Here is the error log: {}".format(str(e)))
            return {"errorMessage": "Couldn't validate the login request."}

    @staticmethod
    def user_exists(userID, firstName, lastName, email, rank, databaseLocation):
        """
        Checks if the user exists in the database.
        :param userID: The user id of the user.
        :param firstName: The first name of the user.
        :param lastName: The last name of the user.
        :param email: The email of the user.
        :param rank: The rank of the user.
        :param databaseLocation: The location of the database.
        :return: True if the user exists and false if it isn't.
        """
        try:
            usersConnection = sqlite3.connect(databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers:
                return {"errorMessage": "The user doesnt exists"}
            else:
                if existingUsers[0][0] == int(userID) and existingUsers[0][1] == firstName and existingUsers[0][2] == lastName and existingUsers[0][3] == email and existingUsers[0][5] == rank:
                    return {"status": "The user exists"}
                else:
                    return {"errorMessage": "The user doesnt exists"}
        except Exception as e:
            print("couldn't check if the user exists " + str(e))
            return {"errorMessage": "couldn't check if the user exists " + str(e)}

    @staticmethod
    def remove_user(email, databaseLocation):
        """
        Removes a user from the database.
        :param email: The email of the user.
        :param databaseLocation: The location of the database.
        :return: The status of the request.
        """
        try:
            usersConnection = sqlite3.connect(databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return {
                    "errorMessage": "There is no user in the database with the email {} or there is more then one user with this email.".format(
                        email)}
            else:
                usersCurser.execute("DELETE FROM users WHERE email = '{}'".format(email))
                usersConnection.commit()
                usersConnection.close()
                return {"status": "Successfully removed user {} from the database".format(email)}
        except Exception as e:
            return {"errorMessage": "Couldn't remove the user from the database" + str(e)}

    @staticmethod
    def get_user_info(email, databaseLocation):
        """
        Getting the user firstname, lastname, email and rank.
        :param email: The email of the user.
        :param databaseLocation: The location of the database.
        :return: A list of the user information.
        """
        try:
            usersConnection = sqlite3.connect(databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return {"errorMessage": "The user doesnt exists"}
            else:
                user = list(existingUsers[0])
                del user[4]
                del user[5]
                return {"status": user}

        except Exception as e:
            print("couldn't check if the user exists " + str(e))
            return {"errorMessage": "couldn't check if the user exists " + str(e)}

    @staticmethod
    def change_tracker(email, tracker, databaseLocation):
        """
        Changing the current tracker in the database
        :param email: The email of the user.
        :param tracker: The tracker we want to change to.
        :param databaseLocation: The location of the database.
        :return: The status of the request.
        """
        try:
            usersConnection = sqlite3.connect(databaseLocation)
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return {"errorMessage": "The user doesnt exists"}
            else:
                usersCurser.execute("UPDATE users SET tracker = '{}' WHERE email = '{}'".format(tracker, email))
                usersConnection.commit()
                usersConnection.close()
                return {"status": "tracker set"}
        except Exception as e:
            print("couldn't check if the user exists " + str(e))
            return {"errorMessage": "couldn't check if the user exists " + str(e)}

    @staticmethod
    def create_database(databaseLocation):
        """
        Create a new database if there isn't a one.
        :param databaseLocation: The location of the database.
        :return: Nothing
        """
        # checking if the databases exist
        if not os.path.isfile(databaseLocation):  # Checking if the file's database exists.
            open(databaseLocation, "x")
            usersConnection = sqlite3.connect(databaseLocation)
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


DBFunctions.register_new_user("admin1", "admin1", "admin@admin.com", "asdfasdf", "asdfasdf", "admin", r"C:\Users\Owner\Desktop\עידו\school\הנדסת תוכנה\PrivateFileSharing\web_server\users.db")