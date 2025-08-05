import json
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends

from app.models.database.logging.request_log import RequestLog
from app.services.database import Database, get_database


class LoggingService:
    def __init__(self, db: Database = None, enabled: bool = True):
        self.db = db
        self.enabled = enabled

    async def log_request(
            self,
            endpoint: str,
            input_data: Dict[str, Any],
            output_data: Optional[Dict[str, Any]] = None,
            status: str = "success",
            error_message: Optional[str] = None
    ) -> Optional[str]:
        if not self.enabled:
            return None

        if self.db is None:
            print("Warning: Database not available for logging")
            return None

        log_id = str(uuid.uuid4())
        try:
            with self.db.get_db() as db:
                log_entry = RequestLog(
                    id=log_id,
                    endpoint=endpoint,
                    input_data=json.dumps(input_data),
                    output_data=json.dumps(output_data) if output_data else None,
                    status=status,
                    error_message=error_message
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            print(f"Failed to log request: {e}")

        return log_id


def get_logging_service(db: Database = Depends(get_database)) -> LoggingService:
    enabled = os.getenv("LOGGING_ENABLED", "true").lower() == "true"

    if not enabled:
        # Return logging service without database when disabled
        return LoggingService(db=None, enabled=False)

    # Use the injected database instance when logging is enabled
    return LoggingService(db=db, enabled=True)
