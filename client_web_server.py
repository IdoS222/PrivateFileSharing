import socket
import flask
import flask_login
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect
import os
from UserFunctions import UserFunctions


class User(flask_login.UserMixin):
    def __init__(self, user_id, firstName, lastName, email, rank, authenticated=False):
        self.user_id = user_id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.rank = rank
        self.authenticated = authenticated
        self.tracker = ["0.0.0.0", 0]

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
        return "{}:{}:{}:{}:{}:{}".format(self.user_id, self.firstName, self.lastName, self.email, self.rank,
                                          self.tracker)


userActive = {}
app = Flask(__name__, template_folder=os.path.join("www", "templates"),
            static_folder=os.path.join("www", "static"))  # App object
app.config['SECRET_KEY'] = 'dashfqh9f8hfwdfkjwefh78y9342h'  # Secret Key
login_manager = LoginManager()  # Login manager object
login_manager.init_app(app)


@app.route('/')
@flask_login.login_required
def index():
    if request.method == "GET":
        try:  # We are trying to connect to the tracker to get all the files before giving the page back to the user.
            user = list(userActive.values())[0]
            tracker = user.tracker

            if tracker[0] == "0.0.0.0":  # This means the user didn't pick a tracker yet
                return render_template("index.html")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(tuple(tracker))
            request = {
                "requestType": 0000,
                "userID": user.user_id,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "email": user.email,
                "rank": user.rank
            }
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
    if answer == "Successfully loged in.":
        info = UserFunctions.get_user_info(request.values["email"])
        userActive[flask.request.values["email"]] = User(info[0], info[1], info[2], info[3], info[4])
        flask_login.login_user(userActive.get(flask.request.values["email"]))
        return redirect('/')
    else:
        return answer


@login_manager.user_loader
def load_user(user_email):
    return userActive.get(user_email)


@app.route("/logout")
def logout():
    userActive.popitem()
    flask_login.logout_user()
    return redirect("/login")


@app.route("/settings", methods=["GET", "POST"])
@flask_login.login_required
def settings():
    if request.method == "GET":
        return render_template("settings.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
