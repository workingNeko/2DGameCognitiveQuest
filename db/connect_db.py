import mysql.connector
from mysql.connector import Error

# =====================================================
# MYSQL DATABASE CONFIGURATION (InfinityFree)
# =====================================================
DB_HOST = "sql113.infinityfree.com"
DB_USER = "if0_42596578"
DB_PASSWORD = "4321Cbaa"
DB_NAME = "if0_42596578_XXX"  # Replace XXX with your specific database name
DB_PORT = 3306


class Database:
    """Database connection and query management class."""
    def __init__(self, host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                connect_timeout=5
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print(f"[DB SUCCESS] Connected to MySQL database '{self.database}' at {self.host}")
                return True
        except Exception as e:
            print(f"[DB WARNING] Database connection failed ({self.host}): {e}")
            self.connection = None
            self.cursor = None
            return False

    def is_connected(self):
        """Check if database connection is active."""
        try:
            return self.connection is not None and self.connection.is_connected()
        except Exception:
            return False

    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results as list of dicts."""
        if not self.is_connected():
            if not self.connect():
                return []
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[DB ERROR] Database Query Error: {e}")
            return []

    def execute_non_query(self, query, params=None):
        """Execute an INSERT / UPDATE / DELETE query and commit."""
        if not self.is_connected():
            if not self.connect():
                return False
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Exception as e:
            print(f"[DB ERROR] Database Non-Query Error: {e}")
            return False

    def close(self):
        """Close database cursor and connection."""
        try:
            if self.cursor:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("[DB INFO] MySQL connection closed.")
        except Exception:
            pass


def connect_db(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT):
    """Helper function to create a new database connection instance."""
    return Database(host=host, user=user, password=password, database=database, port=port)


# Default singleton instance for `from db import db`
db = Database()
