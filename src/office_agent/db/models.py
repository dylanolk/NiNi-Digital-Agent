from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Index, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

def now() -> datetime: return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
UUIDType = Uuid(as_uuid=True)
JSONType = JSON().with_variant(JSONB, "postgresql")
VectorType = Vector(384) if Vector else JSON()

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    products: Mapped[list["Product"]] = relationship(back_populates="manufacturer")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("manufacturer_id", "model", name="uq_products_manufacturer_model"),
        UniqueConstraint("manufacturer_id", "sku", name="uq_products_manufacturer_sku"),
    )
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    manufacturer_id: Mapped[UUID] = mapped_column(ForeignKey("manufacturers.id"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    model: Mapped[str] = mapped_column(String(200), index=True)
    sku: Mapped[str | None] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    manufacturer: Mapped[Manufacturer] = relationship(back_populates="products")
    prices: Mapped[list["ProductPrice"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="product", cascade="all, delete-orphan")

class ProductPrice(Base):
    __tablename__ = "product_prices"
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    vendor: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    source_url: Mapped[str | None] = mapped_column(String(1000))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    product: Mapped[Product] = relationship(back_populates="prices")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(300))
    version: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    storage_key: Mapped[str] = mapped_column(String(1000))
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    product: Mapped[Product] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(VectorType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    document: Mapped[Document] = relationship(back_populates="chunks")
