from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload
from office_agent.db.models import Manufacturer, Product

class ProductRepository:
    def __init__(self, session: Session): self.session = session
    def add(self, product: Product) -> Product:
        self.session.add(product); self.session.flush(); return product
    def manufacturer(self, name: str) -> Manufacturer | None:
        return self.session.scalar(select(Manufacturer).where(Manufacturer.name == name))
    def get_or_create_manufacturer(self, name: str, website_url: str | None = None) -> Manufacturer:
        manufacturer = self.manufacturer(name)
        if manufacturer is None:
            manufacturer = Manufacturer(name=name, website_url=website_url)
            self.session.add(manufacturer)
            self.session.flush()
        elif website_url and not manufacturer.website_url:
            manufacturer.website_url = website_url
        return manufacturer
    def find_by_manufacturer_model(self, manufacturer_id: UUID, model: str) -> Product | None:
        return self.session.scalar(select(Product).where(Product.manufacturer_id == manufacturer_id, Product.model == model))
    def deactivate(self, product_id: UUID) -> Product:
        product = self.get(product_id)
        if product is None: raise ValueError("Unknown product ID")
        product.active = False
        self.session.flush()
        return product
    def get(self, product_id: UUID) -> Product | None:
        return self.session.execute(select(Product).options(joinedload(Product.manufacturer), joinedload(Product.documents)).where(Product.id == product_id)).unique().scalar_one_or_none()
    def search(self, query=None, category=None, manufacturer=None, active_only=True, limit=50) -> list[Product]:
        stmt = select(Product).join(Product.manufacturer).options(joinedload(Product.manufacturer)).distinct()
        if active_only: stmt = stmt.where(Product.active.is_(True))
        if category: stmt = stmt.where(Product.category == category)
        if manufacturer: stmt = stmt.where(Manufacturer.name.ilike(f"%{manufacturer}%"))
        if query:
            q = f"%{query}%"; stmt = stmt.where(or_(Product.name.ilike(q), Product.model.ilike(q), Product.sku.ilike(q), Product.description.ilike(q), Manufacturer.name.ilike(q)))
        return list(self.session.scalars(stmt.limit(min(max(limit, 1), 50))).unique())
