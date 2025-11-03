-- step: create_parent_id_index
CREATE INDEX IF NOT EXISTS idx_chat_branches_parent_id 
ON chat_branches(parent_id);

-- step: rollback
DROP INDEX IF EXISTS idx_chat_branches_parent_id;
