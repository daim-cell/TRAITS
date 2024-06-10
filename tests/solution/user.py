# solution/user.py
import mariadb
from typing import List

class User:
    INSERT_USER_INTO_DB_TEMPLATE = "INSERT INTO User (username, password) VALUES (%s, %s)"
    GET_ALL_USERS_IN_DB_TEMPLATE = "SELECT username, password FROM User"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def insert_into_db(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(self.INSERT_USER_INTO_DB_TEMPLATE, (self.username, self.password))
            connection.commit()
        except mariadb.IntegrityError as e:
            # Re-raise the IntegrityError to match the test's expectations
            raise

    @classmethod
    def get_all_users_in_db(cls, connection) -> List['User']:
        cursor = connection.cursor()
        cursor.execute(cls.GET_ALL_USERS_IN_DB_TEMPLATE)
        return [User(username, password) for username, password in cursor]

    @classmethod
    def set_isolation_level(cls, connection, isolation_level):
        cursor = connection.cursor()
        cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")
        connection.commit()

    def __eq__(self, other):
        return self.username == other.username and self.password == other.password

    def __repr__(self):
        return f"User(username={self.username}, password={self.password})"


