from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MarketplaceModelMixin:
    __syncdateentity__: str
    __uniqueconstraints__: list[str]

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            result[column.name] = value
        return result

    @classmethod
    def column_names(cls) -> list[str]:
        return [column.name for column in cls.__table__.columns]


class OrderModel(Base, MarketplaceModelMixin):
    __tablename__ = "orders"
    __syncdateentity__ = "order"
    __uniqueconstraints__ = ["order_id", "seller_id", "date"]

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    status: Mapped[str] = mapped_column(String(32))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shipping_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    coupon_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OrderPaymentModel(Base, MarketplaceModelMixin):
    __tablename__ = "order_payments"
    __syncdateentity__ = "order_payment"
    __uniqueconstraints__ = ["order_id", "payment_id"]

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(64))
    method: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_at: Mapped[date] = mapped_column(Date)


class ProductModel(Base, MarketplaceModelMixin):
    __tablename__ = "products"
    __syncdateentity__ = "product"
    __uniqueconstraints__ = ["product_id", "product_sku_id", "seller_id", "date"]

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_sku_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sales_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reserved_stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stock_coverage_in_days: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TrafficModel(Base, MarketplaceModelMixin):
    __tablename__ = "traffic"
    __syncdateentity__ = "traffic"
    __uniqueconstraints__ = ["seller_id", "date", "source", "medium"]

    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    source: Mapped[str] = mapped_column(String(128), primary_key=True)
    medium: Mapped[str] = mapped_column(String(128), primary_key=True)
    sessions: Mapped[int] = mapped_column(Integer)
    users: Mapped[int] = mapped_column(Integer)
    pageviews: Mapped[int] = mapped_column(Integer)
