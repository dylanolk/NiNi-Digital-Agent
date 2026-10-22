from decimal import Decimal
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base, Manufacturer, Product, ProductPrice
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.services.product_search import ProductSearchService
from office_agent.services.spreadsheet import SpreadsheetService

def setup():
    e=create_engine("sqlite://"); Base.metadata.create_all(e); s=sessionmaker(bind=e)(); m=Manufacturer(name="Demo"); s.add(m); s.flush(); p=Product(manufacturer_id=m.id,name="Demo AP",model="AP-1",category="access_point",attributes={"poe":True}); s.add(p); s.flush(); s.add(ProductPrice(product_id=p.id,vendor="V",amount=Decimal("200.00"),currency="USD")); s.commit(); return s,p
def test_search_and_spreadsheet(tmp_path):
    s,p=setup(); service=ProductSearchService(ProductRepository(s),PriceRepository(s)); result=service.search(category="access_point"); assert result["results"][0]["price"]["amount"] == "200.00"
    out=SpreadsheetService(service,tmp_path).generate("Demo Office",recommendations=[{"product_id":str(p.id),"quantity":4,"recommendation_reason":"Coverage"}]); assert out["total"] == "800.00"; assert Path(out["download_reference"]).exists()
