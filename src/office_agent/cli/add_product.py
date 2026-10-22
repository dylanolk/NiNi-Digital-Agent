import argparse
from office_agent.db.session import create_schema, get_session
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.services.catalog import CatalogService
def main():
    p=argparse.ArgumentParser(); p.add_argument("--manufacturer",required=True); p.add_argument("--name",required=True); p.add_argument("--model",required=True); p.add_argument("--sku"); p.add_argument("--category",required=True); p.add_argument("--description"); p.add_argument("--attributes",default="{}"); p.add_argument("--website-url"); a=p.parse_args(); create_schema(); s=get_session(); product=CatalogService(ProductRepository(s),PriceRepository(s)).add_product(a.manufacturer,a.name,a.model,a.category,a.sku,a.description,a.attributes,a.website_url); print(product.id)
if __name__ == "__main__": main()
