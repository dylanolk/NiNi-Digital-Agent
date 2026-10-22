import re
from decimal import Decimal, InvalidOperation
from typing import Any

from office_agent.db.models import Product
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService, parse_money


class CatalogImportService:
    """Validate and optionally commit rows supplied by an MCP client."""

    MAX_ROWS = 500

    def __init__(self, products: ProductRepository, prices: PriceRepository):
        self.products, self.prices = products, prices
        self.catalog = CatalogService(products, prices)

    @staticmethod
    def _text(row: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    @staticmethod
    def _category(row: dict[str, Any]) -> str:
        value = CatalogImportService._text(row, "type", "category").lower().replace("-", " ").replace("_", " ")
        aliases = {
            "wireless access point": "access_point", "access point": "access_point", "ap": "access_point",
            "switch": "network_switch", "poe switch": "network_switch", "network switch": "network_switch",
            "firewall": "firewall", "camera": "camera", "door controller": "door_controller",
            "tv": "display", "display": "display", "tv mount": "tv_mount",
            "rally bar": "rally_bar", "rally bar mini": "rally_bar_mini", "conference camera": "conference_camera",
            "labor": "labor", "programming": "labor", "hardware": "hardware", "cabling": "cabling",
        }
        if value in aliases:
            return aliases[value]
        category = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
        return category or "uncategorized"

    def _validate(self, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not isinstance(rows, list) or not rows or len(rows) > self.MAX_ROWS:
            raise ValueError(f"rows must contain between 1 and {self.MAX_ROWS} items")
        valid, errors, seen = [], [], set()
        for number, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                errors.append({"row": number, "error": "Row must be an object"}); continue
            brand, model = self._text(row, "brand", "manufacturer"), self._text(row, "model", "name")
            if not brand or not model:
                errors.append({"row": number, "error": "Brand and model are required"}); continue
            key = (brand.casefold(), model.casefold())
            if key in seen:
                errors.append({"row": number, "error": "Duplicate brand/model in import"}); continue
            seen.add(key)
            price = row.get("price")
            if price not in (None, ""):
                try:
                    amount = parse_money(price)
                except (InvalidOperation, ValueError):
                    errors.append({"row": number, "brand": brand, "model": model, "error": "Invalid price"}); continue
            else:
                amount = None
            valid.append({"row": number, "brand": brand, "name": model, "model": model,
                          "category": self._category(row), "price": str(amount) if amount is not None else None,
                          "currency": str(row.get("currency") or "USD").upper(),
                          "supplier": self._text(row, "supplier", "vendor") or None,
                          "source_url": self._text(row, "link", "source_url") or None,
                          "description": self._text(row, "note", "description") or None,
                          "attributes": {"source_category": self._text(row, "category"),
                                         "source_type": self._text(row, "type"),
                                         "shipping": row.get("shipping"),
                                         "needs_mount": row.get("needs_mount"),
                                         "needs_power": row.get("needs_power")}})
        return valid, errors

    def preview(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        valid, errors = self._validate(rows)
        existing, new = [], []
        for item in valid:
            maker = self.products.manufacturer(item["brand"])
            product = None
            if maker:
                product = self.products.find_by_manufacturer_model(maker.id, item["model"])
            (existing if product else new).append(item)
        return {"rows_received": len(rows), "valid_rows": len(valid), "new_products": len(new),
                "existing_products": len(existing), "skipped_rows": len(errors), "errors": errors,
                "proposed_rows": valid}

    def commit(self, rows: list[dict[str, Any]], confirmation: str) -> dict[str, Any]:
        if confirmation.strip() != "APPROVE IMPORT":
            raise ValueError('Explicit confirmation required: type "APPROVE IMPORT"')
        preview = self.preview(rows)
        if preview["errors"]:
            raise ValueError("Import has validation errors; correct them and retry")
        created = prices = 0
        for item in preview["proposed_rows"]:
            maker = self.products.get_or_create_manufacturer(item["brand"])
            product = self.products.find_by_manufacturer_model(maker.id, item["model"])
            if product is None:
                product = self.catalog.add_product(item["brand"], item["name"], item["model"], item["category"],
                                                    description=item["description"], attributes=item["attributes"])
                created += 1
            if item["price"] is not None and item["supplier"]:
                self.catalog.add_price(product.id, item["supplier"], Decimal(item["price"]), item["currency"], item["source_url"], notes=item["description"])
                prices += 1
        return {"committed": True, "products_created": created, "prices_added": prices,
                "existing_products_updated": preview["existing_products"]}
