import asyncio
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from office_agent.db.models import Base
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService

def test_stdio_client_handshake_and_tool_call(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'client.db').as_posix()}"
    engine = create_engine(database_url); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)(); catalog = CatalogService(ProductRepository(session), PriceRepository(session)); product = catalog.add_product("ClientCo", "Client AP", "CAP-1", "access_point"); catalog.add_price(product.id, "Client Vendor", "123.45")
    environment = os.environ.copy(); environment.update({"PYTHONPATH": str((__import__('pathlib').Path.cwd() / "src").resolve()), "DATABASE_URL": database_url, "EMBEDDING_PROVIDER": "hash"})
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "office_agent.mcp.server"], env=environment, cwd=str(__import__('pathlib').Path.cwd()))

    async def exercise():
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                tools = await client.list_tools()
                assert {tool.name for tool in tools.tools} == {"search_products", "get_product", "search_user_manuals", "generate_recommendations_xlsx"}
                result = await client.call_tool("search_products", {"category": "access_point"})
                assert not result.is_error and "CAP-1" in str(result.content)
    asyncio.run(exercise())
