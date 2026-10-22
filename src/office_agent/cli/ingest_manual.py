import argparse
import asyncio
from uuid import UUID
from office_agent.config import settings
from office_agent.db.session import create_schema, get_session
from office_agent.repositories.documents import DocumentRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.embeddings import build_embedding_provider
from office_agent.services.manual_ingestion import ManualIngestionService
from office_agent.services.storage import LocalFileStorage

def main():
    parser = argparse.ArgumentParser(description="Ingest a product PDF manual")
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--type", dest="document_type", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--title")
    parser.add_argument("--version")
    args = parser.parse_args(); create_schema(); session = get_session()
    service = ManualIngestionService(DocumentRepository(session), LocalFileStorage(settings.local_storage_path), build_embedding_provider())
    document, created = asyncio.run(service.ingest(UUID(args.product_id), args.file, args.document_type, args.title, args.source_url, args.version))
    print(f"{document.id} ({'created' if created else 'duplicate'})")

if __name__ == "__main__": main()
