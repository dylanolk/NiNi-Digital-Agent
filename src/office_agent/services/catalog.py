import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID
from office_agent.db.models import Product, ProductPrice
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository

def parse_money(value: str | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid decimal number") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be a finite, non-negative decimal")
    return amount.quantize(Decimal("0.01"))

def parse_attributes(value: str | dict) -> dict:
    if isinstance(value, dict): return value
    try: parsed = json.loads(value)
    except json.JSONDecodeError as exc: raise ValueError("Attributes must be valid JSON") from exc
    if not isinstance(parsed, dict): raise ValueError("Attributes must be a JSON object")
    return parsed

class CatalogService:
    def __init__(self, products: ProductRepository, prices: PriceRepository): self.products, self.prices = products, prices
    def add_product(self, manufacturer: str, name: str, model: str, category: str, sku: str | None = None, description: str | None = None, attributes: str | dict = "{}", website_url: str | None = None) -> Product:
        if not manufacturer.strip() or not name.strip() or not model.strip() or not category.strip(): raise ValueError("Manufacturer, name, model, and category are required")
        maker = self.products.get_or_create_manufacturer(manufacturer.strip(), website_url)
        product = Product(manufacturer_id=maker.id, name=name.strip(), model=model.strip(), sku=sku.strip() if sku else None, category=category.strip(), description=description, attributes=parse_attributes(attributes))
        self.products.add(product); self.products.session.commit(); return product
    def add_price(self, product_id: UUID, vendor: str, amount: str | Decimal, currency: str = "USD", source_url: str | None = None, effective_at: datetime | None = None, notes: str | None = None) -> ProductPrice:
        if not vendor.strip(): raise ValueError("Vendor is required")
        if len(currency) != 3: raise ValueError("Currency must be a 3-letter code")
        if self.products.get(product_id) is None: raise ValueError("Unknown product ID")
        price = ProductPrice(product_id=product_id, vendor=vendor.strip(), amount=parse_money(amount), currency=currency.upper(), source_url=source_url, effective_at=effective_at, notes=notes)
        self.prices.add(price); self.prices.session.commit(); return price
