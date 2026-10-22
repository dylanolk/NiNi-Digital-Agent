# Office Technology Recommendation Agent

This is a backend-only office technology catalog and manual-evidence service. An external LLM (ChatGPT, Claude, or another MCP client) performs reasoning and orchestration; this application provides structured product/price tools, provenance-preserving manual retrieval, and deterministic XLSX generation. It does not call an LLM.

## Local setup

1. Install Python 3.12+ and [uv](https://docs.astral.sh/uv/).
2. Copy `.env.example` to `.env`.
3. Start PostgreSQL with `docker compose up -d`.
4. Run `uv sync` and `uv run python -m office_agent.cli.seed_demo`.
5. Start MCP with `uv run python -m office_agent.mcp.server`.

The default embedding provider is a deterministic offline hash provider for development and the lightweight container image. Install the optional embedding extra with `uv sync --extra embeddings`, then set `EMBEDDING_PROVIDER=sentence_transformers` to use `all-MiniLM-L6-v2`. The embedding interface is isolated so it can later be replaced.

## Catalog and manuals

Add products with `uv run python -m office_agent.cli.add_product --manufacturer Demo --name "Switch" --model SW-1 --category network_switch --attributes '{"poe":true}'`. Add price history with `uv run python -m office_agent.cli.add_price --product-id ID --vendor "Vendor A" --amount 699.00`; each price is a new row. Deactivate a product without deleting it using `uv run python -m office_agent.cli.deactivate_product --product-id ID`. Ingest a PDF with `uv run python -m office_agent.cli.ingest_manual --product-id ID --type installation_guide --file ./manual.pdf --source-url https://example.test/manual.pdf`. It stores the original under `data/manuals`, extracts each PDF page with PyMuPDF, chunks text, embeds chunks, and retains document/page provenance.

## MCP and output

The four tools are `search_products`, `get_product`, `search_user_manuals`, and `generate_recommendations_xlsx`. Set `MCP_TRANSPORT=streamable-http` for the hosted transport; the endpoint path is `/mcp`. For the container workflow, `docker compose up --build` runs migrations and starts the application on `http://127.0.0.1:8000/mcp`. Local workbooks appear under `data/exports`. Remote deployments should put the endpoint behind HTTPS and OAuth/OIDC, with private object storage and short-lived download references; the current reference deployment is not production authentication.

### Claude

For local development, configure a compatible Claude MCP connection to launch `python -m office_agent.mcp.server` with `PYTHONPATH=src` and the project environment. For a hosted connector, use the shared HTTPS `/mcp` endpoint. Claude-specific prompts or business logic are not required.

### ChatGPT

Configure a custom MCP app/connector against the hosted HTTPS `/mcp` endpoint. The server must be internet-reachable and authenticated for remote use. The standard MCP tool schemas are sufficient; no ChatGPT-specific UI or Apps SDK is required for V1.

## Tests

Run `uv run pytest`. Tests should use a disposable database and synthetic PDFs; no external manufacturer documents are required.

## Deployment direction

The application is intentionally one portable Python service backed by PostgreSQL/pgvector and a storage abstraction. PostgreSQL and storage should remain private. Authentication/authorization belongs at the MCP protected-resource boundary and can be added without changing catalog, retrieval, or spreadsheet services.

## Production authentication

Set `MCP_AUTH_ENABLED=true` only after configuring an external OAuth/OIDC provider. Provide `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`, and the public `MCP_RESOURCE_URL`; optionally set `AUTH_REQUIRED_SCOPES` as a comma-separated list. The MCP server validates signed JWT bearer tokens and required scopes through the official SDK boundary. The application does not store passwords or implement an identity provider. Keep `MCP_AUTH_ENABLED=false` for local development only. Anonymous production access is not supported.
