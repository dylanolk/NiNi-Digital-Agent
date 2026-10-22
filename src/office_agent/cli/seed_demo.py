from decimal import Decimal
from office_agent.db.models import Manufacturer, Product, ProductPrice
from office_agent.db.session import create_schema, get_session
def main():
    create_schema(); s=get_session()
    data=[("DemoNet","Demo AP 1","DN-AP1","access_point",{"poe":True,"poe_standard":"PoE+","max_power_watts":20},200), ("DemoNet","Demo AP 2","DN-AP2","access_point",{"poe":True,"poe_standard":"PoE+","max_power_watts":25},220), ("DemoNet","Demo Switch 1","DN-SW1","network_switch",{"poe":True,"poe_budget_watts":200,"ports":24},600), ("DemoNet","Demo Switch 2","DN-SW2","network_switch",{"poe":True,"poe_budget_watts":370,"ports":48},900), ("DemoView","Demo Display 1","DV-55","display",{"size_inches":55},700), ("DemoView","Demo Display 2","DV-75","display",{"size_inches":75},1200), ("DemoMount","Demo Mount 1","DM-400","tv_mount",{"vesa":"400x400"},120), ("DemoMount","Demo Mount 2","DM-600","tv_mount",{"vesa":"600x400"},180), ("DemoConf","Demo Camera 1","DC-1","conference_camera",{"resolution":"4K"},850)]
    for maker,name,model,category,attrs,amount in data:
        m=s.query(Manufacturer).filter_by(name=maker).first() or Manufacturer(name=maker); s.add(m); s.flush();
        if not s.query(Product).filter_by(manufacturer_id=m.id,model=model).first():
            pr=Product(manufacturer_id=m.id,name=name,model=model,category=category,attributes=attrs); s.add(pr); s.flush(); s.add(ProductPrice(product_id=pr.id,vendor="Demo Vendor",amount=Decimal(amount),currency="USD"))
    s.commit()
if __name__ == "__main__": main()
