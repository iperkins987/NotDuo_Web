import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import messaging
from dataclasses import dataclass
import time
import uuid
import hashlib

@dataclass
class NotDuoUser:
    """
    Data class to represent a user in the NotDuo authentication system.

    Attributes:
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        username (str): The user's username.
    """
    first_name: str
    last_name: str
    username: str


class NotDuoAuthenticator:
    """
    Class to handle authentication using the NotDuo system.

    Attributes:
        service_account_key_path (str): Path to the Firebase service account key.
        db_url (str): URL of the Firebase Realtime Database.
        time_threshold (int): Maximum time (in seconds) to wait for an authentication response.
    """

    def __init__(self, service_account_key_path: str, db_url: str, time_threshold: int = 10):
        """
        Initialize the NotDuoAuthenticator.

        Args:
            service_account_key_path (str): Path to the Firebase service account key.
            db_url (str): URL of the Firebase Realtime Database.
            time_threshold (int): Maximum time (in seconds) to wait for an authentication response.
        """
        self.credentials = credentials.Certificate(service_account_key_path)
        self.time_threshold = time_threshold

        firebase_admin.initialize_app(self.credentials, {
            "databaseURL": db_url
        })

    def __check_password(self, password: str, user_ref: db.Reference) -> bool:
        """
        Check if the provided password matches the user's stored password hash.

        Args:
            password (str): The password to check.
            user_ref (db.Reference): Reference to the user's data in the database.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_password = user_ref.get()["passwordHash"]

        return (password_hash == user_password)

    def __send_notification(self, user_ref: db.Reference):
        """
        Send a notification to the user's device to request authentication.

        Args:
            user_ref (db.Reference): Reference to the user's data in the database.
        """
        # Build the notification
        message = messaging.Message(
            notification=messaging.Notification(
                title="NotDuo Authentication",
                body="Please verify a login attempt!",
            ),
            token=user_ref.get()["deviceToken"]
        )

        # Send the notification
        response = messaging.send(message)

    def __add_auth_request(self, user_ref: db.Reference) -> str:
        """
        Add an authentication request to the user's data in the database.

        Args:
            user_ref (db.Reference): Reference to the user's data in the database.

        Returns:
            str: The unique identifier for the authentication request.
        """
        uid = str(uuid.uuid4().int)
        user_ref.update({"authToken": uid})

        return uid

    def __reset_auth_response(self, user_ref: db.Reference):
        """
        Reset the authentication response in the user's data in the database.

        Args:
            user_ref (db.Reference): Reference to the user's data in the database.
        """
        user_ref.update({"responseToken": "NO_TOKEN"})

    def __get_auth_response(self, uid: str, user_ref: db.Reference) -> str:
        """
        Wait for the authentication response from the user's device.

        Args:
            uid (str): The unique identifier for the authentication request.
            user_ref (db.Reference): Reference to the user's data in the database.

        Returns:
            str: The response token received from the user's device.
        """
        time_passed = 0
        auth_response = user_ref.get()["responseToken"]

        # Wait for the response
        while (auth_response != uid):
            time.sleep(1)

            # Update the response
            auth_response = user_ref.get()["responseToken"]

            time_passed += 1

            # Timeout
            if (time_passed > self.time_threshold):
                break

        self.__reset_auth_response(user_ref)

        return auth_response

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate a user based on their username and password.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating whether the authentication was successful and an error message if applicable.
        """
        is_auth = False
        user_ref = db.reference(f"users/{username}")
        error_message = "User does not exist!"

        # Check if this user exists
        if (user_ref.get() != None):
            error_message = "Incorrect password!"

            # Check if the password is correct
            if (self.__check_password(password, user_ref)):
                error_message = "NotDuo failed to respond!"

                # Notify the registered NotDuo device of the login attempt
                self.__send_notification(user_ref)

                # Collect auth tokens for the attempt
                auth_token = self.__add_auth_request(user_ref)
                auth_response = self.__get_auth_response(auth_token, user_ref)

                # Check if the login attempt was successful
                if (auth_token == auth_response):
                    error_message = ""
                    is_auth = True

        return (is_auth, error_message)

    def get_auth_user(self, username: str) -> NotDuoUser:
        """
        Retrieve a NotDuoUser object based on their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            NotDuoUser: The retrieved user, or None if the user does not exist.
        """
        notduo_user = None
        user_obj = db.reference(f"users/{username}").get()

        # Check if this user exists
        if (user_obj != None):
            notduo_user = NotDuoUser(
                user_obj["firstName"],
                user_obj["lastName"],
                user_obj["username"]
            )

        return notduo_user