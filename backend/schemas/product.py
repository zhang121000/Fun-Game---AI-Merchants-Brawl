from pydantic import BaseModel


class MerchantOut(BaseModel):
    id: int
    name: str
    ai_model: str
    main_category: str = ""
    persona_prompt: str = ""
    brand_color: str
    brand_style: dict
    is_active: bool

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    id: int
    merchant_id: int
    name: str
    description: str
    ai_model: str = ""
    target_demographic: str
    category: str
    price: float
    original_price: float
    stock: int
    image_url: str
    ai_selling_points: list
    is_active: bool

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    target_demographic: str
    category: str
    price: float
    original_price: float
    stock: int = 100
