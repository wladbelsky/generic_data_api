from clickhouse_sqlalchemy import engines
from clickhouse_sqlalchemy.types import Nullable
from sqlalchemy import Column, String, DateTime, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RequestLog(Base):
    __tablename__ = 'request_logs'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    endpoint = Column(String(255))
    input_data = Column(Text)
    output_data = Column(Nullable(Text), nullable=True)
    status = Column(String(50))
    error_message = Column(Nullable(Text), nullable=True)

    __table_args__ = (
        engines.MergeTree(order_by=('timestamp', 'id')),
    )
