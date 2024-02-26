import flask_login


class User(flask_login.UserMixin):
    def __init__(self, user_id, firstName, lastName, email, rank, authenticated=False):
        self.user_id = user_id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email  # unique id
        self.rank = rank
        self.authenticated = authenticated
    def is_active(self):
        """
        :return: True because all users are active
        """
        return True

    def get_id(self):
        """
        :return: The email of the user.
        """
        return self.email

    def is_authenticated(self):
        """
        :return: True if the user is authenticated and false if he isn't.
        """
        return self.authenticated

    def is_anonymous(self):
        """
        :return: False
        """
        return False

    def __str__(self):
        return "{}:{}:{}:{}:{}".format(self.user_id, self.firstName, self.lastName, self.email, self.rank)
