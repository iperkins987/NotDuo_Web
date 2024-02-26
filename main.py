from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import messaging
import hashlib
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
    user_ref = db.reference(f"Users/{username}")
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
            title="Hey Hey Hey!",
            body="Its Fat Albert!!"
        ),
        token=user.device_token
    )

    # Send the notification
    response = messaging.send(message)
    print('Successfully sent message:', response)


@app.route("/")
@app.route("/login", methods=["POST"])
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
                sendNotification(user)
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