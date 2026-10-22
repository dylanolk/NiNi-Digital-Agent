import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from office_agent.db.session import create_schema, get_session
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.services.catalog import CatalogService
def main():
    p=argparse.ArgumentParser(); p.add_argument("--product-id",required=True); p.add_argument("--vendor",required=True); p.add_argument("--amount",required=True); p.add_argument("--currency",default="USD"); p.add_argument("--source-url"); p.add_argument("--effective-at"); p.add_argument("--notes"); a=p.parse_args(); create_schema(); s=get_session(); CatalogService(ProductRepository(s),PriceRepository(s)).add_price(UUID(a.product_id),a.vendor,a.amount,a.currency,a.source_url,datetime.fromisoformat(a.effective_at) if a.effective_at else None,a.notes)
if __name__ == "__main__": main()
