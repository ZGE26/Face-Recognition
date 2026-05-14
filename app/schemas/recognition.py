from datetime import datetime
from pydantic import BaseModel


class ScanResponse(BaseModel):
    recognized: bool
    user_id: int | None = None
    name: str | None = None
    employee_id: str | None = None
    confidence: float | None = None
    scanned_at: datetime
