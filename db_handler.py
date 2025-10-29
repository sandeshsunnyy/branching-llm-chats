import psycopg
import os
from dotenv import load_dotenv

# Load variables from our .env file (like POSTGRES_PASSWORD)
load_dotenv()

# --- This is the SQL command we designed ---
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_branches (
    branch_id UUID PRIMARY KEY,
    parent_id UUID REFERENCES chat_branches(branch_id),
    new_messages JSONB NOT NULL,
    parent_message_count_at_branch INTEGER,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# --- SQL command to add the index for speed ---
CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chat_branches_parent_id 
ON chat_branches(parent_id);
"""

try:
    # Try to connect to the database
    conn = psycopg.connect(
        host="localhost",
        dbname="langgraph_chat",
        user="sandesh",
        password=os.environ.get("POSTGRES_PASSWORD")
    )
    
    print("Connection successful!")
    
    # --- New code to create the table ---
    
    # 1. Get a cursor
    with conn.cursor() as cur:
        # 2. Execute the CREATE TABLE command
        cur.execute(CREATE_TABLE_SQL)
        print("Table 'chat_branches' checked/created successfully.")
        
        # 3. Execute the CREATE INDEX command
        cur.execute(CREATE_INDEX_SQL)
        print("Index 'idx_chat_branches_parent_id' checked/created successfully.")
    
    # 4. Commit the changes to make them permanent
    conn.commit()
    
    # We can close the connection
    conn.close()

except psycopg.OperationalError as e:
    print(f"Unable to connect to the database: {e}")
except Exception as e:
    print(f"An error occurred: {e}")