from datetime import datetime
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from office_agent.db.models import ProductPrice
class PriceRepository:
    def __init__(self, session: Session): self.session = session
    def add(self, price: ProductPrice) -> ProductPrice:
        self.session.add(price); self.session.flush(); return price
    def latest(self, product_id: UUID) -> ProductPrice | None:
        return self.session.scalar(select(ProductPrice).where(ProductPrice.product_id == product_id).order_by(desc(ProductPrice.captured_at), desc(ProductPrice.effective_at)).limit(1))
    def history(self, product_id: UUID) -> list[ProductPrice]:
        return list(self.session.scalars(select(ProductPrice).where(ProductPrice.product_id == product_id).order_by(desc(ProductPrice.captured_at))))
