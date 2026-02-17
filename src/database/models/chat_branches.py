from sqlalchemy import Index 
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import TEXT, ForeignKey
from src.database.base import Base, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class ChatBranches(Base, TimestampMixin):
    __tablename__ = "chat_branches"

    __table_args__ = (
        Index('idx_chat_branches_parent_id', 'parent_id'),
    )

    branch_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )

    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_branches.branch_id", ondelete="RESTRICT"),
        nullable=True
    )

    new_messages: Mapped[dict] = mapped_column(
        JSONB,
        default=dict
    )

    parent_message_count_at_branch: Mapped[int] = mapped_column()

    summary: Mapped[str] = mapped_column(TEXT)