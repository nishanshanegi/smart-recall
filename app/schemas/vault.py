#API Shape:-> This is what the user sees.
from pydantic import BaseModel
from typing import Optional

class IngestRequest(BaseModel):
    content_type: str
    content: str
    title: Optional[str] = None