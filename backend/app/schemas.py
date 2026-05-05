from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ProductBase(BaseModel):
    title: str
    description: str
    price: float
    image_url: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItem(CartItemBase):
    id: int
    product: Product
    class Config:
        from_attributes = True

class CartBase(BaseModel):
    pass

class Cart(CartBase):
    id: int
    user_id: int
    items: List[CartItem] = []
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    total_amount: float

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    user_id: int
    status: str
    payment_id: Optional[str] = None
    class Config:
        from_attributes = True

class CheckoutResponse(BaseModel):
    order: Order
    url_pago: Optional[str] = None

class PaymentIntent(BaseModel):
    amount: float
    description: str
    email: str
