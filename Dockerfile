FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/src
ENV MCP_HOST=0.0.0.0
ENV MCP_TRANSPORT=streamable-http
EXPOSE 8000
CMD ["python", "-m", "office_agent.mcp.server"]
