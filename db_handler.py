import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_branches (
    branch_id UUID PRIMARY KEY NOT NULL,
    parent_id UUID REFERENCES chat_branches(branch_id),
    new_messages JSONB NOT NULL,
    parent_message_count_at_branch INTEGER,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chat_branches_parent_id 
ON chat_branches(parent_id);
"""

try:
    conn = psycopg.connect(
        host="localhost",
        dbname="langgraph_chats",
        user="sandeshsunny",
    )
    
    print("Connection successful!")
    
    with conn.cursor() as cur:

        cur.execute(CREATE_TABLE_SQL)
        print("Table 'chat_branches' checked/created successfully.")

        cur.execute(CREATE_INDEX_SQL)
        print("Index 'idx_chat_branches_parent_id' checked/created successfully.")

    conn.commit()

    conn.close()

except psycopg.OperationalError as e:
    print(f"Unable to connect to the database: {e}")
except Exception as e:
    print(f"An error occurred: {e}")