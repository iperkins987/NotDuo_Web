from flask import Flask, render_template, request, redirect, url_for
from NotDuoAuthentication import *

# Flask and NotDuoAuthenticator setup
app = Flask(__name__)
notduo_auth = NotDuoAuthenticator("serviceAccountKey.json", "https://notduo-99e30-default-rtdb.firebaseio.com")


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

        # Attempt to authenticate with NotDuo
        is_auth, notduo_user = notduo_auth.authenticate(username, password)

        if (is_auth):
            return render_template("home.html", user=notduo_user)

    return render_template("login.html", error=error)


if __name__ == "__main__":
    app.run(debug=True)