class User:
    def __init__(self, username, first_name, last_name, password_hash, device_token) -> None:
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.device_token = device_token