"""MCP protocol adapter. Domain logic lives in services, not here."""
import logging
from typing import Any
from office_agent.config import settings
from office_agent.db.session import get_session
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.documents import DocumentRepository
from office_agent.services.product_search import ProductSearchService
from office_agent.services.manual_search import ManualSearchService
from office_agent.services.embeddings import HashEmbeddingProvider
from office_agent.services.spreadsheet import SpreadsheetService
from office_agent.services.catalog_import import CatalogImportService
from office_agent.services.storage import LocalFileStorage
from office_agent.auth import OIDCJWTTokenVerifier

try:
    from mcp.server import MCPServer  # MCP SDK v2 high-level server
except ImportError:  # Allows the domain package to be tested without MCP installed.
    class MCPServer:
        def __init__(self, name: str): self.name, self.tools = name, {}
        def tool(self, *args, **kwargs):
            def decorator(fn): self.tools[fn.__name__] = fn; return fn
            return decorator

logger = logging.getLogger(__name__)

def _auth_configuration():
    if not settings.mcp_auth_enabled: return {}
    required = [scope.strip() for scope in settings.auth_required_scopes.split(",") if scope.strip()]
    values = [settings.oidc_issuer_url, settings.oidc_audience, settings.oidc_jwks_url, settings.mcp_resource_url]
    if any(value is None for value in values):
        raise RuntimeError("MCP auth requires OIDC_ISSUER_URL, OIDC_AUDIENCE, OIDC_JWKS_URL, and MCP_RESOURCE_URL")
    from pydantic import AnyHttpUrl
    from mcp.server.auth.settings import AuthSettings
    auth = AuthSettings(issuer_url=AnyHttpUrl(settings.oidc_issuer_url), resource_server_url=AnyHttpUrl(settings.mcp_resource_url), required_scopes=required or None)
    verifier = OIDCJWTTokenVerifier(settings.oidc_issuer_url, settings.oidc_audience, settings.oidc_jwks_url, required)
    return {"auth": auth, "token_verifier": verifier}

mcp = MCPServer("office-technology-agent", **_auth_configuration())

def _services():
    session = get_session()
    products = ProductSearchService(ProductRepository(session), PriceRepository(session))
    manuals = ManualSearchService(DocumentRepository(session), HashEmbeddingProvider())
    sheets = SpreadsheetService(products, settings.local_storage_path / "exports")
    return session, products, manuals, sheets

def _import_service():
    session = get_session()
    return session, CatalogImportService(ProductRepository(session), PriceRepository(session))

@mcp.tool()
async def search_products(query: str | None = None, category: str | None = None, manufacturer: str | None = None, min_price: str | None = None, max_price: str | None = None, attributes: dict[str, Any] | None = None, active_only: bool = True, limit: int = 10):
    """Search the active structured catalog; prices are latest-known values."""
    session, products, _, _ = _services()
    try: return products.search(query, category, manufacturer, min_price, max_price, attributes, active_only, limit)
    finally: session.close()

@mcp.tool()
async def get_product(product_id: str):
    """Retrieve one product, its latest price, and document metadata."""
    session, products, _, _ = _services()
    try: return products.get(product_id)
    finally: session.close()

@mcp.tool()
async def search_user_manuals(query: str, product_ids: list[str] | None = None, manufacturer: str | None = None, document_types: list[str] | None = None, limit: int = 10):
    session, _, manuals, _ = _services()
    try: return await manuals.search(query, product_ids, manufacturer, document_types, limit)
    finally: session.close()

@mcp.tool()
async def generate_recommendations_xlsx(project_name: str, client_name: str | None = None, notes: str | None = None, recommendations: list[dict[str, Any]] | None = None):
    session, _, _, sheets = _services()
    try: return sheets.generate(project_name, client_name, notes, recommendations)
    finally: session.close()

@mcp.tool()
async def preview_catalog_import(rows: list[dict[str, Any]]):
    """Validate spreadsheet rows without changing the catalog. Always preview before commit."""
    session, importer = _import_service()
    try: return importer.preview(rows)
    finally: session.close()

@mcp.tool()
async def commit_catalog_import(rows: list[dict[str, Any]], confirmation: str):
    """Commit previously previewed catalog rows after explicit user approval."""
    session, importer = _import_service()
    try: return importer.commit(rows, confirmation)
    finally: session.close()

def main():
    logging.basicConfig(level=settings.log_level, stream=__import__('sys').stderr)
    # The SDK owns transport details; business services are transport-independent.
    mcp.run(transport=settings.mcp_transport, host=settings.mcp_host, port=settings.mcp_port)
if __name__ == "__main__": main()
