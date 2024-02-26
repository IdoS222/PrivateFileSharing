import re
import sqlite3
import os
import random
import string
import argon2


class UserFunctions:
    @staticmethod
    def create_database():
        """
        Create a new database if there isn't a one.
        :return: Nothing
        """
        # checking if the databases exist
        if not os.path.isfile('Databases/users.db'):  # Checking if the file's database exists.
            open("Databases/users.db", "x")
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("""CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    firstName TEXT,
                    lastName TEXT,
                    email TEXT,
                    passHash TEXT,
                    rank TEXT,
                    salt TEXT
            )""")

            usersConnection.commit()
            usersConnection.close()

    @staticmethod
    def register_new_user(firstName, lastName, email, password, confirmPassword, rank):
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
            return "The first name is too short."
        if len(lastName) <= 2:
            return "The last name if too short."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "The email is illegal."
        if len(password) <= 5:
            return "The password is too short"
        if password != confirmPassword:
            return "The password and the confirm password dont match"

        # Hash the password using the argon2 algorithm.
        passHasher = argon2.PasswordHasher()
        salt = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=32))
        passHash = passHasher.hash(password + salt)

        try:  # registering the user in the database
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers:  # if it goes into this condition, it means the list is empty and there is no user with this email, and we can proceed with adding the user to the database
                command = "INSERT INTO users (firstName, lastName, email, passHash, rank, salt) VALUES ('{}', '{}', '{}', '{}', '{}', '{}')"
                usersCurser.execute(command.format(firstName, lastName, email, passHash, rank, salt))
                usersConnection.commit()
                usersConnection.close()
                return "Successfully register the user {} to the database.".format(email)
            else:
                return "There is a user with this email. please change the email or log in."
        except Exception as e:
            print("Couldn't add the user {} from the database. Here is the error log: {}".format(firstName, str(e)))
            return "Couldn't add the user {} from the database. Here is the error log: {}".format(firstName, str(e))

    @staticmethod
    def process_login(email, password):
        """
        Process the login request from the user
        :param email: The email of the user
        :param password: The password of the user
        :return: True if the login is successful and false if it isn't
        """

        # Hash the password using the argon2 algorithm.
        passHasher = argon2.PasswordHasher()

        try:
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search

            if not existingUsers or len(existingUsers) > 1:
                return "The user doesnt exists"
            else:
                try:
                    password = password + existingUsers[0][6]  # add the salt to the password
                    passHasher.verify(existingUsers[0][4], password)  # verify the password
                    return "Successful login."
                except Exception:
                    return "The password is wrong."
        except Exception as e:
            print("Couldn't validate the login request. Here is the error log: {}".format(str(e)))
            return "Couldn't validate the login request."

    @staticmethod
    def user_exists(userID, firstName, lastName, email, rank):
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
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers:
                return False
            else:
                if len(existingUsers) > 1:
                    return False
                else:
                    if existingUsers[0][0] == userID and existingUsers[0][1] == firstName and existingUsers[0][
                        2] == lastName and existingUsers[0][3] == email and existingUsers[0][5] == rank:
                        return True
                    else:
                        return False
        except Exception as e:
            print("couldn't check if the user exists " + str(e))
            return False

    @staticmethod
    def remove_user(email):
        """
        Removes a user from the database.
        :param email: The email of the user.
        :return: The status of the request.
        """
        try:
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return "There is no user in the database with the email {} or there is more then one user with this email.".format(
                    email)
            else:
                usersCurser.execute("DELETE FROM users WHERE email = '{}'".format(email))
                usersConnection.commit()
                usersConnection.close()
                return "Successfully removed user {} from the database".format(email)
        except Exception as e:
            print("Couldn't remove the user from the database" + str(e))
            return "Couldn't remove the user from the database" + str(e)

    @staticmethod
    def get_user_info(email):
        """
        Getting the user firstname, lastname, email and rank.
        :param email: The email of the user.
        :return: A list of the user information.
        """
        try:
            usersConnection = sqlite3.connect("Databases/users.db")
            usersCurser = usersConnection.cursor()

            usersCurser.execute("SELECT * FROM users WHERE email = '{}'".format(
                email))  # Trying to check for users with the same email.
            existingUsers = usersCurser.fetchall()  # The result of the search
            if not existingUsers or len(existingUsers) >= 2:
                return "The user doesnt exists"
            else:
                user = list(existingUsers[0])
                del user[4]
                del user[5]
                return user

        except Exception as e:
            print("couldn't check if the user exists " + str(e))
            return False