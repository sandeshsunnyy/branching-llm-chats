import psycopg
from psycopg.connection import Connection
from dotenv import load_dotenv

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
    
def check_for_branch_entry(branch_id) -> bool | None:
    try:
        conn = connect_to_db()
        query = "SELECT EXISTS(SELECT 1 FROM chat_branches WHERE id = %s)"
        conn.execute(query, (branch_id,))
        exists = conn.fetchone()[0]
        return exists
    
    except psycopg.OperationalError as e:
        print(f"Unable to query database. Error while checking for branch entry: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to check for branch entry: {e}")
        return None
        
        
def close_connection(conn: Connection) -> None:

    try:
        conn.close()
    except psycopg.OperationalError as e:
        print(f"Unable to close connection: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to close: {e}")
        return None
    
