"""initial office agent schema"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    uid = postgresql.UUID(as_uuid=True)
    js = postgresql.JSONB()
    op.create_table("manufacturers", sa.Column("id",uid,primary_key=True), sa.Column("name",sa.String(200),nullable=False,unique=True), sa.Column("website_url",sa.String(1000)), sa.Column("created_at",sa.DateTime(timezone=True)), sa.Column("updated_at",sa.DateTime(timezone=True)))
    op.create_table("products", sa.Column("id",uid,primary_key=True), sa.Column("manufacturer_id",uid,sa.ForeignKey("manufacturers.id"),nullable=False), sa.Column("name",sa.String(300),nullable=False), sa.Column("model",sa.String(200),nullable=False), sa.Column("sku",sa.String(200)), sa.Column("category",sa.String(100),nullable=False), sa.Column("description",sa.Text), sa.Column("active",sa.Boolean,nullable=False,server_default=sa.true()), sa.Column("attributes",js,nullable=False,server_default="{}"), sa.Column("created_at",sa.DateTime(timezone=True)), sa.Column("updated_at",sa.DateTime(timezone=True)), sa.UniqueConstraint("manufacturer_id","model",name="uq_products_manufacturer_model"), sa.UniqueConstraint("manufacturer_id","sku",name="uq_products_manufacturer_sku"))
    op.create_table("product_prices", sa.Column("id",uid,primary_key=True), sa.Column("product_id",uid,sa.ForeignKey("products.id"),nullable=False), sa.Column("vendor",sa.String(200),nullable=False), sa.Column("amount",sa.Numeric(12,2),nullable=False), sa.Column("currency",sa.String(3),nullable=False), sa.Column("source_url",sa.String(1000)), sa.Column("captured_at",sa.DateTime(timezone=True)), sa.Column("effective_at",sa.DateTime(timezone=True)), sa.Column("notes",sa.Text))
    op.create_table("documents", sa.Column("id",uid,primary_key=True), sa.Column("product_id",uid,sa.ForeignKey("products.id"),nullable=False), sa.Column("document_type",sa.String(60),nullable=False), sa.Column("title",sa.String(300),nullable=False), sa.Column("version",sa.String(100)), sa.Column("source_url",sa.String(1000)), sa.Column("storage_key",sa.String(1000),nullable=False), sa.Column("checksum",sa.String(64),nullable=False), sa.Column("retrieved_at",sa.DateTime(timezone=True)), sa.Column("created_at",sa.DateTime(timezone=True)), sa.Column("updated_at",sa.DateTime(timezone=True)))
    op.create_table("document_chunks", sa.Column("id",uid,primary_key=True), sa.Column("document_id",uid,sa.ForeignKey("documents.id"),nullable=False), sa.Column("chunk_index",sa.Integer,nullable=False), sa.Column("page_number",sa.Integer), sa.Column("section",sa.String(300)), sa.Column("content",sa.Text,nullable=False), sa.Column("embedding",Vector(384)), sa.Column("created_at",sa.DateTime(timezone=True)))
def downgrade():
    for table in ("document_chunks","documents","product_prices","products","manufacturers"): op.drop_table(table)
