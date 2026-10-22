"""add manufacturer SKU uniqueness"""
from alembic import op
revision = "0002_catalog_constraints"
down_revision = "0001_initial"
branch_labels = None
depends_on = None
def upgrade():
    op.create_unique_constraint("uq_products_manufacturer_sku", "products", ["manufacturer_id", "sku"])
def downgrade():
    op.drop_constraint("uq_products_manufacturer_sku", "products", type_="unique")
