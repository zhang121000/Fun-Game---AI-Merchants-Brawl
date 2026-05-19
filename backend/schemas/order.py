from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_id: int
    merchant_id: int
    total_amount: float
    status: str
    is_simulated: bool
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    customer_id: int
    items: list[CartItemOut] = []

    class Config:
        from_attributes = True


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateCartRequest(BaseModel):
    quantity: int
