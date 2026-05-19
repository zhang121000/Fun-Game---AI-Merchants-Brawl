from pydantic import BaseModel


class CustomerOut(BaseModel):
    id: int
    demographic: str
    name: str | None = None
    age_range: str
    preferences: dict
    purchase_weight: float
    is_star: bool = False

    class Config:
        from_attributes = True
