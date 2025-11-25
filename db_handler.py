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
        print("Connection successful!")

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
            print("Postgres connection closed successfully")
    

def check_for_branch_entry(branch_id) -> bool | None:
    try:
        conn = connect_to_db()
        query = "SELECT EXISTS(SELECT 1 FROM chat_branches WHERE branch_id = %s)"
        cursor = conn.cursor()
        cursor.execute(query, (branch_id,))
        exists = cursor.fetchone()[0]
        close_connection(conn=conn, cursor=cursor)
        return exists
    
    except psycopg.OperationalError as e:
        print(f"Unable to query database. Error while checking for branch entry: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to check for branch entry: {e}")
        return None
    finally:
        print("Safely closing postgres Connection")
        if conn:
            close_connection(conn=conn)
            print("postgres connection closed successfully.")

        
def insert_chat(branch_id: uuid.UUID, parent_id: uuid.UUID | None, new_messages: dict, parent_message_count_at_branch: int | None, summary: str) -> bool:
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
            print("Postgres connection closed successfully")
