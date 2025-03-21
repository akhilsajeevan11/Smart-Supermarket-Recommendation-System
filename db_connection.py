import os
import mysql.connector
from mysql.connector import Error, IntegrityError
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env in parent directory
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Db:
    def __init__(self):
        self.connection = None
        self.cursor = None
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', 'root'),
                database=os.getenv('DB_NAME', 'super_market_recomendation_system'),
                port=int(os.getenv('DB_PORT', 3306)),
                auth_plugin=os.getenv('DB_AUTH_PLUGIN', 'mysql_native_password')
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.connection.autocommit = False  # Disable auto-commit
        except Error as err:
            logging.error(f"Database connection failed: {err}")
            raise

    def commit(self):
        """Commit the current transaction"""
        try:
            self.connection.commit()
        except Error as err:
            self.connection.rollback()
            logging.error(f"Commit failed: {err}")
            raise

    def rollback(self):
        """Roll back the current transaction"""
        try:
            self.connection.rollback()
        except Error as err:
            logging.error(f"Rollback failed: {err}")
            raise

    def execute(self, query, params=None):
        """For INSERT/UPDATE/DELETE operations without auto-commit"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.rowcount
        except Error as err:
            self.rollback()
            logging.error(f"Query execution failed: {err}")
            raise

    def select(self, query, params=None):
        """For SELECT operations returning multiple rows"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as err:
            logging.error(f"Select query failed: {err}")
            raise

    def selectOne(self, query, params=None):
        """For SELECT operations returning single row"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as err:
            logging.error(f"SelectOne query failed: {err}")
            raise

    def insert(self, query, values):
        """For INSERT operations returning lastrowid without auto-commit"""
        try:
            self.cursor.execute(query, values)
            return self.cursor.lastrowid
        except Error as err:
            self.rollback()
            logging.error(f"Insert query failed: {err}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def __del__(self):
        self.close()
