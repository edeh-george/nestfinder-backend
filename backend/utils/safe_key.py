from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

datetime_file = './last_access.txt'
key_file = './key.txt'


class AccessTimeManager:
    def __init__(self, datetime_file):
        self.datetime_file = datetime_file
        self._last_access = datetime.now()
        self.load_access_time()

    @property
    def last_access(self):
        return self._last_access

    @last_access.setter
    def last_access(self, value):
        if isinstance(value, datetime):
            self._last_access = value
            self.save_access_time()
        else:
            raise ValueError("last_access must be a datetime object")

    def load_access_time(self):
        if os.path.exists(self.datetime_file):
            with open(self.datetime_file, "r") as file:
                content = file.readlines()
                if content:
                    self._last_access = datetime.fromisoformat(content[-1].strip())
                file.close()
        else:
            with open(self.datetime_file, 'w') as file:
                self._last_access = datetime.now()
                self.save_access_time()


    def save_access_time(self):
        with open(self.datetime_file, "w+") as file:
            file.write(f"\n{self._last_access.isoformat()}")
            file.close()

manager = AccessTimeManager(datetime_file)

class KeyManager:
    def __init__(self, key_file):
        self.key_file = key_file
        self._key = None
        self.load_key()


    @property
    def key(self):
        """The key property."""
        return self._key

    @key.setter
    def key(self, value):
        self._key = value
        self.save_key()

    def load_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "r") as file:
                content = file.readlines()
                if content:
                    self._key = content[-1].strip().encode()
                else:
                    self._key = Fernet.generate_key()
                    self.save_key()
        else:
            self._key = Fernet.generate_key()
            self.save_key()

    def save_key(self):
        with open(self.key_file, "w+") as file:
            file.write(f"{self._key.decode()}\n")

key_manager = KeyManager(key_file)
key_manager.load_key

def generate_safe_key():
    key = key_manager.key
    last_access = manager.last_access
    print({'key': key, 'last_access': last_access})
    current_time = datetime.fromisoformat(datetime.now().isoformat())
    difference = current_time - last_access
    if difference > timedelta(seconds=600) and difference > timedelta(days=2):
        key = Fernet.generate_key()
        key_manager.key = key
        manager.last_access = datetime.now()
    return key

generate_safe_key()