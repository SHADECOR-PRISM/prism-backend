from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ProjectRead(BaseModel):
    id: UUID
    name: str
    total_budget: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)