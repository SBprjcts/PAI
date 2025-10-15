# db_operations.py
import psycopg2
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from Backend.Models.user import User
# import datetime
# from Tools.db_syntax import sqlToObject
import os
from typing import Optional
from psycopg2 import Binary
from werkzeug.security import check_password_hash


def getDbConnection():
    # hostname = '192.168.2.255'    # Private IP
    hostname = '76.71.0.245'    # Public IP
    database = 'PAIdb'
    username = 'paiadmin'
    password = 'Pai@124'
    port_id = 5432
    conn = psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=password,
        port=port_id
    )
    return conn


def get_sql_file_path(filename):
    # Get the directory of the current file (operations.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Move up one directory to the project root, then into the 'Database/sql' directory
    sql_dir = os.path.join(current_dir, '..', 'Database', 'sql')
    # Join the SQL directory with the filename
    file_path = os.path.join(sql_dir, filename)
    return file_path


def add_users(user: User) -> bool:
    conn = getDbConnection()
    cur = conn.cursor()
    # Define the path to your SQL file
    sql_file_path = get_sql_file_path('add_users.sql')
    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        insert_query = file.read()
    # Set new user id as len(users) table (number of users) + 1:
    user.id = get_users_count() + 1
    # Execute the query with parameters from the `user` object
    cur.execute(insert_query, (user.id, user.company, user.email, user.password))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_users(email: str, password: str) -> Optional[User]:
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('get_users.sql')
    # Read the SQL command from the file
    with open(sql_file_path, 'r') as file:
        get_query = file.read()
    # Execute the query with parameters from the `user` object
    cur.execute(get_query, (email, ))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    stored_hash = row[3]
    if not check_password_hash(stored_hash, password):
        return None

    # return a User with the same fields you used before
    return User(row[1], row[2], stored_hash, row[0])


def get_users_count():
    conn = getDbConnection()
    cur = conn.cursor()
    sql_file_path = get_sql_file_path('get_users_count.sql')
    with open(sql_file_path, 'r') as file:
        get_query = file.read()
    cur.execute(get_query)
    count = cur.fetchone()[0]
    return count
