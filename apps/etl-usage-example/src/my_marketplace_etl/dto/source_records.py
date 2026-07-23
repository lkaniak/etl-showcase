from typing import Any

from pydantic import BaseModel, Field


class OrderPaymentRecord(BaseModel):
    order_id: str | None = None
    payment_id: str | None = None
    seller_id: str | None = None
    method: str | None = None
    paymentMethod: str | None = None
    amount: Any = None
    paid_at: Any = None


class OrderRecord(BaseModel):
    order_id: str | None = None
    seller_id: str | None = None
    date: Any = None
    status: str | None = None
    total_amount: Any = None
    customer_state: str | None = None
    customer_city: str | None = None
    shipping_state: str | None = None
    shipping_city: str | None = None
    coupon_code: str | None = None
    coupon_name: str | None = None
    payments: list[dict | OrderPaymentRecord] = Field(default_factory=list)
    legacy_field: str | None = None


class TrafficRecord(BaseModel):
    seller_id: str | None = None
    date: Any = None
    sessions: Any = None
    users: Any = None
    pageviews: Any = None
    source: str | None = None
    medium: str | None = None


class ProductsRecord(BaseModel):
    seller_id: str | None = None
    product_id: str | None = None
    product_sku_id: str | None = None
    date: Any = None
    product_category_name: str | None = None
    product_sub_category_name: str | None = None
    product_department_name: str | None = None
    product_brand: str | None = None
    product_price: Any = None
    product_sold_quantity: Any = None
    product_stock_quantity: Any = None
    product_stock_reserved_quantity: Any = None
    product_stock_coverage_days: Any = None
