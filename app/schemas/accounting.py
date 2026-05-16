from pydantic import BaseModel
from typing import Literal

class Container(BaseModel):
    id: str
    user_id: str
    project_name: str
    category: str
    applied_at: str
    status: Literal["pending", "approved", "rejected"]
    total_amount: int
