from typing import Any, Dict

from pydantic import BaseModel


class ProcessDataResponse(BaseModel):
    received_data: Dict[str, Any]
    cat_fact: Dict[str, Any]
