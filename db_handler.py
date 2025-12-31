import psycopg
from psycopg.connection import Connection
from dotenv import load_dotenv
import uuid
import json

load_dotenv()

def connect_to_db() -> Connection | None:
    
    try:
        conn = psycopg.connect(
            host="localhost",
            dbname="langgraph_chats",
            user="sandeshsunny",
        )
        return conn

    except psycopg.OperationalError as e:
        print(f"Unable to connect to the database: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to connect to database: {e}")
        return None
    
def close_connection(conn: Connection, cursor: psycopg.Cursor = None) -> None:

    try:
        if cursor:
            cursor.close()
        conn.close()
    except psycopg.OperationalError as e:
        print(f"Unable to close connection: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to close: {e}")
        return None
    
    finally:
        if conn:
            conn.close()
    

def check_for_branch_entry(branch_id) -> bool | None:
    try:
        conn = connect_to_db()
        query = "SELECT EXISTS(SELECT 1 FROM chat_branches WHERE branch_id = %s)"
        cursor = conn.cursor()
        cursor.execute(query, (branch_id,))
        try:
            exists = cursor.fetchone()[0]
        except TypeError as e:
            print("Tried fetching but found none. Returning None.")
            return None
        close_connection(conn=conn, cursor=cursor)
        return exists
    
    except psycopg.OperationalError as e:
        print(f"Unable to query database. Error while checking for branch entry: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to check for branch entry: {e}")
        return None
    finally:
        if conn:
            close_connection(conn=conn)

def insert_chat(branch_id: uuid.UUID, parent_id: uuid.UUID | None, new_messages: dict, parent_message_count_at_branch: int | None, summary: str) -> bool:
    """
    To be used if in some scenario, initiate_chat was not invoked.
    """
    conn = connect_to_db()
    query = "INSERT INTO chat_branches (branch_id, parent_id, new_messages, parent_message_count_at_branch, summary) VALUES (%s, %s, %s, %s, %s)"
    new_messages_json = json.dumps(new_messages, indent=2)
    try: 
        cursor = conn.cursor()
        inputs = (branch_id, parent_id, new_messages_json, parent_message_count_at_branch, summary)
        cursor.execute(query, inputs)
        conn.commit()
        close_connection(conn=conn, cursor=cursor)
        return True
    except psycopg.OperationalError as e:
        print(f"Unable to query database. Error while inserting new branch entry: {e}")
        return False
    except Exception as e:
        print(f"An error occurred while inserting new DB entry {e}")
        return False
    finally:
        if conn:
            close_connection(conn=conn)

def initiate_chat(branch_id: uuid.UUID, parent_id: uuid.UUID = None, parent_message_count_at_branch: int = None) -> bool:
    conn = connect_to_db()
    query = "INSERT INTO chat_branches (branch_id, parent_id, parent_message_count_at_branch) VALUES (%s, %s, %s)"
    try: 
        cursor = conn.cursor()
        inputs = (branch_id, parent_id, parent_message_count_at_branch)
        cursor.execute(query, inputs)
        conn.commit()
        close_connection(conn=conn, cursor=cursor)
        return True
    except psycopg.OperationalError as e:
        print(f"Unable to query database. Error while inserting new branch entry: {e}")
        return False
    except Exception as e:
        print(f"An error occurred while inserting new DB entry {e}")
        return False
    finally:
        if conn:
            close_connection(conn=conn)

def retrieve_messages(branch_id: uuid.UUID):
    conn = connect_to_db()
    query = "SELECT new_messages FROM chat_branches WHERE branch_id = %s"
    try:
        cursor = conn.cursor()
        cursor.execute(query, (branch_id,))
        try:
            fetched_messages = cursor.fetchone()[0]
        except TypeError as e:
            print("Tried fetching but found none. Returning None")
            return None
        close_connection(conn=conn, cursor=cursor)
        return fetched_messages
    except psycopg.OperationalError as e:
        print(f"Unable to fetch message:  {e}")
        return False
    except Exception as e:
        print(f"An error occurred while fetching messages: {e}")
        return False
    finally:
        if conn:
            close_connection(conn=conn)

def retrieve_data_for_resuming_chat() -> list:
    conn = connect_to_db()
    query = "SELECT branch_id, new_messages, summary FROM chat_branches WHERE parent_id IS NULL"
    try:
        cursor = conn.cursor()
        cursor.execute(query=query)
        try:
            fetched_rows = cursor.fetchall()
        except TypeError as e:
            print("Tried fetching data for continuing chats. But failed. Returning None")
            return None
        close_connection(conn=conn, cursor=cursor)
        return fetched_rows

    except psycopg.OperationalError as e:
        print(f"Unable to fetch convo data:  {e}")
        return None
    except Exception as e:
        print(f"An error occurred while data to continue convo: {e}")
        return None
    finally:
        if conn:
            close_connection(conn=conn)


def updata_chat(branch_id: uuid.UUID, messages: dict, summary: str = None) -> bool:
    conn = connect_to_db()
    messages_json = json.dumps(messages, indent=2)
    if summary is None:
        query = "UPDATE chat_branches SET new_messages = %s WHERE branch_id = %s"
        inputs = (messages_json, branch_id)
    else:
        query = "UPDATE chat_branches SET new_messages = %s, summary = %s WHERE branch_id = %s"
        inputs = (messages_json, summary, branch_id)
    try:
        cursor = conn.cursor()
        cursor.execute(query, inputs)
        conn.commit()
        close_connection(conn=conn, cursor=cursor)
        return True
    except psycopg.OperationalError as e:
        print(f"Unable to update message:  {e}")
        return False
    except Exception as e:
        print(f"An error occurred while updating messages: {e}")
        return False
    finally:
        if conn:
            close_connection(conn=conn)
