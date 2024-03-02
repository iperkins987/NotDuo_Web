from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import messaging
import hashlib
import uuid
import time
from User import User

# Flask setup
app = Flask(__name__)

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://notduo-99e30-default-rtdb.firebaseio.com"
})


def getUser(username):

    # Get the user reference from the db
    user_ref = db.reference(f"users/{username}")
    user_obj = user_ref.get()

    # We found the user
    if (user_obj is not None):

        # Create the user object
        user = User(
            user_obj.get("username"),
            user_obj.get("firstName"),
            user_obj.get("lastName"),
            user_obj.get("passwordHash"),
            user_obj.get("deviceToken"))

        return user

    return None


def isValidPassword(user, password):
    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Compare passwords
    return (user.password_hash == password_hash)


def sendNotification(user):

    # Build the notification
    message = messaging.Message(
        notification=messaging.Notification(
            title="NotDuo Authentication",
            body="Please verify a login attempt!",
        ),
        token=user.device_token
    )

    # Send the notification
    response = messaging.send(message)


def AddAuthRequest(user, uid):
    user_ref = db.reference(f"users/{user.username}")
    user_ref.update({"authToken": str(uid)})


def GetAuthResponse(user, uid):
    user_ref = db.reference(f"users/{user.username}/responseToken")
    token = user_ref.get()

    while (token != uid):
        time.sleep(1)
        user_ref = db.reference(f"users/{user.username}/responseToken")
        print("UID IS", token)
        print("RESPONSE TOKEN IS", token)
        token = user_ref.get()


    return True


def resetAuthResponse(user):
    user_ref = db.reference(f"users/{user.username}")
    user_ref.update({"responseToken": "NO_TOKEN"})


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    error = ""

    # If we clicked submit on the form
    if (request.method == "POST"):

        # Get the username and password
        username = request.form["username"]
        password = request.form["password"]

        # See if that user exists
        user = getUser(username)

        if (user is not None):

            # Check if their password is correct
            if (isValidPassword(user, password)):

                uid = str(uuid.uuid4().int)
                print("UID IS", uid)
                sendNotification(user)
                AddAuthRequest(user, uid)

                if (GetAuthResponse(user, uid)):
                    resetAuthResponse(user)
                    return redirect(url_for("home"))
            else:
                error = "Incorrect Password!"
        else:
            error = "User does not exist!"

    return render_template("login.html", error=error)


@app.route("/home")
def home():
    return "Welcome home user!"


if __name__ == "__main__":
    app.run(debug=True)