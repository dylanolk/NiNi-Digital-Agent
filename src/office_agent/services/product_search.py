from decimal import Decimal, InvalidOperation
from uuid import UUID
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
class PriceService:
    def __init__(self, prices): self.prices = prices
    def latest(self, product_id):
        p = self.prices.latest(product_id)
        return None if not p else {"amount": str(p.amount), "currency": p.currency, "vendor": p.vendor, "captured_at": p.captured_at.isoformat(), "source_url": p.source_url}
class ProductSearchService:
    def __init__(self, products, prices): self.products = products; self.price_service = PriceService(prices)
    def _result(self, p):
        return {"product_id": str(p.id), "manufacturer": p.manufacturer.name, "name": p.name, "model": p.model, "sku": p.sku, "category": p.category, "description": p.description, "attributes": p.attributes or {}, "price": self.price_service.latest(p.id)}
    def search(self, query=None, category=None, manufacturer=None, min_price=None, max_price=None, attributes=None, active_only=True, limit=10):
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("Limit must be an integer between 1 and 50")
        try:
            minimum = Decimal(str(min_price)) if min_price is not None else None
            maximum = Decimal(str(max_price)) if max_price is not None else None
        except InvalidOperation as exc: raise ValueError("Price filters must be valid decimal numbers") from exc
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("min_price cannot exceed max_price")
        if attributes is not None and not isinstance(attributes, dict): raise ValueError("Attributes must be an object")
        # MCP clients commonly send human-facing category labels rather than
        # the canonical catalog enum (for example, "wireless access point").
        # Normalize those labels before querying the repository.
        category = self._canonical_category(category, query)
        if category and query and self._category_phrase(query):
            query = None
        # Fetch the bounded candidate set before applying price filters so a cheap
        # match is not lost behind unrelated products that happen to sort first.
        results = [self._result(p) for p in self.products.search(query, category, manufacturer, active_only, limit=50)]
        def ok(r):
            price = r["price"]
            if minimum is not None and (not price or Decimal(price["amount"]) < minimum): return False
            if maximum is not None and (not price or Decimal(price["amount"]) > maximum): return False
            return all(r["attributes"].get(k) == v for k,v in (attributes or {}).items())
        return {"results": [r for r in results if ok(r)][:min(limit, 50)]}

    @staticmethod
    def _category_phrase(value):
        text = str(value).strip().lower().replace("-", " ").replace("_", " ")
        return any(alias in text for alias in ("access point", "wireless ap", "poe switch", "network switch", "tv mount", "conference camera"))

    @classmethod
    def _canonical_category(cls, category, query):
        value = category or (query if cls._category_phrase(query) else None)
        if not value:
            return category
        text = str(value).strip().lower().replace("-", " ").replace("_", " ")
        aliases = {
            "access point": "access_point", "wireless access point": "access_point", "wireless ap": "access_point", "ap": "access_point",
            "network switch": "network_switch", "poe switch": "network_switch", "switch": "network_switch",
            "tv mount": "tv_mount", "television mount": "tv_mount", "conference camera": "conference_camera",
        }
        return aliases.get(text, category)
    def get(self, product_id):
        try: parsed_id = UUID(str(product_id))
        except (ValueError, AttributeError, TypeError) as exc: raise ValueError("Unknown product ID") from exc
        p = self.products.get(parsed_id)
        if not p: raise ValueError("Unknown product ID")
        return {**self._result(p), "documents": [{"document_id": str(d.id), "title": d.title, "document_type": d.document_type, "source_url": d.source_url} for d in p.documents]}
