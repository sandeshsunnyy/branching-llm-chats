CREATE TABLE IF NOT EXISTS chat_branches (
    branch_id UUID PRIMARY KEY,
    parent_id UUID REFERENCES chat_branches(branch_id),
    new_messages JSONB NOT NULL,
    parent_message_count_at_branch INTEGER,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS chat_branches;
