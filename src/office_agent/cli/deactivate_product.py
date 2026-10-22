import argparse
from uuid import UUID
from office_agent.db.session import create_schema, get_session
from office_agent.repositories.products import ProductRepository
def main():
    parser = argparse.ArgumentParser(description="Deactivate a catalog product")
    parser.add_argument("--product-id", required=True)
    args = parser.parse_args(); create_schema(); session = get_session(); product = ProductRepository(session).deactivate(UUID(args.product_id)); session.commit(); print(product.id)
if __name__ == "__main__": main()
