from pydantic import BaseModel
from typing import Literal

class UserProfile(BaseModel):
    user_id: str
    user_name: str
    account_type: Literal["Admin", "General"]
    current_date: str