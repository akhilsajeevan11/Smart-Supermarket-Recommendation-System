import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env in parent directory
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Db:
    def __init__(self):
        self.connection = None
        self.cursor = None
        try:
            self.connection = mysql.connector.connect(
                host="localhost",  
                user="root",       
                password="root", 
                database="super_market_recomendation_system",
                port=3306,
                auth_plugin='mysql_native_password'
            )
            self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            print(f"Used credentials: {os.getenv('DB_USER')}@{os.getenv('DB_HOST')}")  # Debug
            raise

    def execute(self, query, params=None):
        """For INSERT/UPDATE/DELETE operations"""
        self.cursor.execute(query, params or ())
        self.connection.commit()
        return self.cursor.rowcount

    def select(self, query, params=None):
        """For SELECT operations returning multiple rows"""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()

    def selectOne(self, query, params=None):
        """For SELECT operations returning single row"""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()

    def insert(self, query, values):
        """For INSERT operations returning lastrowid"""
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Insert error: {err}")
            self.connection.rollback()
            raise
        finally:
            if self.cursor:
                self.cursor.close()
            self.cursor = self.connection.cursor()

    def __del__(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
        except AttributeError:
            pass
        
        try:
            if hasattr(self, 'connection') and self.connection.is_connected():
                self.connection.close()
        except AttributeError:
            pass
