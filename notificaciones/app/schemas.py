from pydantic import BaseModel, EmailStr
from typing import List

class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class EmailPurchaseRequest(BaseModel):
    email: EmailStr
    name: str
    order_id: int
    date: str
    products: List[dict]
    total: float

class EmailPaymentRequest(BaseModel):
    email: EmailStr
    transaction_id: str
    status: str
    date: str
    amount: float
    summary: str

class SmsUploadRequest(BaseModel):
    phone_number: str
    filename: str
    date: str
    used_space: str
    available_space: str
