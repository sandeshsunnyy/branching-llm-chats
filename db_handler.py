import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg.connect(
        host="localhost",  
        dbname="langgraph_chat",  
        user="sandesh",           
        password=os.environ.get("POSTGRES_PASSWORD")
    )
    
    print("Connection successful!")
    
    conn.close()

except psycopg.OperationalError as e:
    print(f"Unable to connect to the database: {e}")