from pydantic import BaseModel


class ExternalAPIResponse(BaseModel):
    fact: str
    length: int
