from sqlalchemy import Column, Integer, TEXT, TIMESTAMP, ForeignKey, BOOLEAN
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index

Base = declarative_base()

class ChatBranches(Base):
    __tablename__ = "chat_branches"

    __table_args__ = (
        Index('idx_chat_branches_parent_id', 'parent_id'),
    )

    branch_id = Column("branch_id", UUID, primary_key=True)
    parent_id = Column("parent_id", UUID, ForeignKey("chat_branches.branch_id"))
    new_messages = Column("new_messages", JSONB, nullable=False)
    parent_message_count_at_branch = Column("parent_message_count_at_branch", Integer)
    summary = Column("summary", TEXT)
    created_at = Column("created_at", TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column("is_active", BOOLEAN, default=True)
    
