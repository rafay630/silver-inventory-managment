"""
End-to-End Manufacturing Flow Test
Tests the complete flow: Login → Create Items → BOM → Production Order → WIP → Expense → Complete → Sell
"""
import requests
import json

BASE = "http://localhost:8000/api"


def test():
    print("═══ END-TO-END MANUFACTURING ERP TEST ═══\n")

    # 1. Login
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✓ Login OK — role: {r.json()['user']['role']}")

    # 2. Get UOM and Warehouse IDs
    uoms = requests.get(f"{BASE}/uom", headers=headers).json()
    uom_g = next(u for u in uoms if u["abbreviation"] == "g")
    uom_pcs = next(u for u in uoms if u["abbreviation"] == "pcs")
    print(f"✓ UOMs loaded — {len(uoms)} UOMs")

    warehouses = requests.get(f"{BASE}/warehouses", headers=headers).json()
    wh = warehouses[0]
    print(f"✓ Warehouse: {wh['name']} ({wh['id'][:8]}...)")

    # 3. Create Raw Materials
    silver = requests.post(f"{BASE}/items", headers=headers, json={
        "name": "Silver 925", "sku": "SLV-925", "item_type": "raw_material",
        "uom_id": uom_g["id"], "base_cost": 2.50, "reorder_level": 100
    }).json()
    assert "id" in silver, f"Create silver failed: {silver}"
    print(f"✓ Raw Material created: {silver['name']} (SKU: {silver['sku']})")

    stone = requests.post(f"{BASE}/items", headers=headers, json={
        "name": "Cubic Zirconia Stone", "sku": "CZ-STONE", "item_type": "raw_material",
        "uom_id": uom_pcs["id"], "base_cost": 0.50
    }).json()
    print(f"✓ Raw Material created: {stone['name']}")

    # 4. Create Finished Good
    ring = requests.post(f"{BASE}/items", headers=headers, json={
        "name": "Silver Ring 925", "sku": "RING-925", "item_type": "finished_good",
        "uom_id": uom_pcs["id"], "base_cost": 0
    }).json()
    print(f"✓ Finished Good created: {ring['name']}")

    # 5. Stock In (Manual Opening Balance) via Stock Ledger
    # We need to record stock entries — let me use the opening balance reference
    from app.database import SessionLocal
    from app.services.stock_ledger_service import StockLedgerService

    db = SessionLocal()
    company_id = requests.get(f"{BASE}/auth/me", headers=headers).json()["company_id"]

    StockLedgerService.record_entry(
        db, company_id, silver["id"], wh["id"],
        qty_in=500, qty_out=0, unit_cost=2.50,
        reference_type="opening_balance", reference_id="OPENING",
        description="Opening balance for Silver 925"
    )
    StockLedgerService.record_entry(
        db, company_id, stone["id"], wh["id"],
        qty_in=200, qty_out=0, unit_cost=0.50,
        reference_type="opening_balance", reference_id="OPENING",
        description="Opening balance for CZ Stones"
    )
    db.commit()
    print("✓ Opening stock recorded: 500g Silver, 200 pcs CZ Stones")

    # Check balances
    bal_silver = StockLedgerService.get_stock_balance(db, company_id, silver["id"], wh["id"])
    bal_stone = StockLedgerService.get_stock_balance(db, company_id, stone["id"], wh["id"])
    assert bal_silver == 500, f"Expected 500, got {bal_silver}"
    assert bal_stone == 200, f"Expected 200, got {bal_stone}"
    print(f"✓ Stock balances verified: Silver={bal_silver}g, Stones={bal_stone}pcs")

    # 6. Create BOM
    bom = requests.post(f"{BASE}/bom/", headers=headers, json={
        "product_id": ring["id"],
        "version": "v1.0",
        "is_active": True,
        "notes": "Standard silver ring with CZ stone",
        "items": [
            {"raw_item_id": silver["id"], "quantity": 10, "wastage_percent": 5},
            {"raw_item_id": stone["id"], "quantity": 1, "wastage_percent": 0},
        ]
    }).json()
    assert "id" in bom, f"Create BOM failed: {bom}"
    print(f"✓ BOM created: {bom['version']} for {ring['name']}")

    # 7. Create Production Order (10 rings)
    po = requests.post(f"{BASE}/production-orders/", headers=headers, json={
        "product_id": ring["id"],
        "bom_id": bom["id"],
        "order_qty": 10,
        "warehouse_id": wh["id"],
        "notes": "First batch of silver rings"
    }).json()
    assert "id" in po, f"Create PO failed: {po}"
    print(f"✓ Production Order created: {po['order_number']} — status: {po['status']}")

    # 8. Start Production
    r = requests.post(f"{BASE}/production-orders/{po['id']}/start", headers=headers)
    assert r.status_code == 200, f"Start PO failed: {r.text}"
    print(f"✓ Production started: {r.json()['status']}")

    # 9. Issue Materials to WIP
    wip = requests.post(f"{BASE}/production-orders/{po['id']}/wip-issues", headers=headers, json={
        "production_order_id": po["id"],
        "issue_date": "2026-02-20",
        "items": [
            {"item_id": silver["id"], "warehouse_id": wh["id"], "quantity": 105},  # 10 rings * 10g * 1.05 wastage
            {"item_id": stone["id"], "warehouse_id": wh["id"], "quantity": 10},
        ]
    }).json()
    assert "id" in wip, f"WIP issue failed: {wip}"
    print(f"✓ WIP Issue: {wip['issue_number']} — materials issued to production")

    # 10. Record Production Expense
    exp = requests.post(f"{BASE}/production-orders/{po['id']}/expenses", headers=headers, json={
        "production_order_id": po["id"],
        "expense_type": "direct_labor",
        "amount": 50.00,
        "expense_date": "2026-02-20",
        "description": "Polishing labor"
    }).json()
    assert "id" in exp, f"Expense failed: {exp}"
    print(f"✓ Expense recorded: {exp['expense_type']} — ${exp['amount']}")

    # 11. Complete Production
    completion = requests.post(f"{BASE}/production-orders/{po['id']}/complete", headers=headers, json={
        "completed_qty": 10,
        "completion_date": "2026-02-20"
    }).json()
    assert "unit_cost" in completion, f"Completion failed: {completion}"
    print(f"✓ Production completed:")
    print(f"  Material cost: ${completion['total_material_cost']:.2f}")
    print(f"  Expenses: ${completion['total_expenses']:.2f}")
    print(f"  Total cost: ${completion['total_production_cost']:.2f}")
    print(f"  Unit cost: ${completion['unit_cost']:.2f} per ring")
    print(f"  Status: {completion['status']}")

    # 12. Verify Finished Goods Stock
    db2 = SessionLocal()
    fg_balance = StockLedgerService.get_stock_balance(db2, company_id, ring["id"], wh["id"])
    fg_wac = StockLedgerService.get_weighted_average_cost(db2, company_id, ring["id"], wh["id"])
    print(f"✓ FG Stock: {fg_balance} rings @ ${fg_wac:.2f}/ring")

    # 13. Sell 5 rings
    sale = requests.post(f"{BASE}/sales/", headers=headers, json={
        "customer_name": "Jewelry Store A",
        "order_date": "2026-02-20",
        "items": [{
            "item_id": ring["id"],
            "warehouse_id": wh["id"],
            "quantity": 5,
            "unit_price": 80.00,
        }],
        "notes": "First sale"
    }).json()
    assert "id" in sale, f"Sale failed: {sale}"
    print(f"✓ Sale: {sale['order_number']} to {sale.get('customer_name', 'N/A')}")
    print(f"  Revenue: ${float(sale.get('total_amount', 0)):.2f}")
    print(f"  COGS: ${float(sale.get('total_cost', 0)):.2f}")

    # 14. Reports
    print("\n═══ REPORTS ═══")

    # Inventory Valuation
    inv = requests.get(f"{BASE}/reports/inventory-valuation", headers=headers).json()
    print(f"\n✓ Inventory Valuation ({len(inv)} items):")
    for item in inv:
        print(f"  {item['item_name']}: {item['balance']} @ ${item['weighted_avg_cost']:.2f} = ${item['total_value']:.2f}")

    # Production Cost Sheet
    cost = requests.get(f"{BASE}/reports/production-cost-sheet/{po['id']}", headers=headers).json()
    print(f"\n✓ Cost Sheet for {cost.get('order_number', 'N/A')}:")
    print(f"  Material cost: ${cost.get('total_material_cost', 0):.2f}")
    print(f"  Expenses: ${cost.get('total_expenses', 0):.2f}")
    print(f"  Unit cost: ${cost.get('unit_cost', 0):.2f}")

    # Trial Balance
    tb = requests.get(f"{BASE}/reports/trial-balance", headers=headers).json()
    print(f"\n✓ Trial Balance:")
    print(f"  Total Debits: ${tb.get('total_debit', 0):.2f}")
    print(f"  Total Credits: ${tb.get('total_credit', 0):.2f}")
    print(f"  BALANCED: {tb.get('is_balanced', False)}")

    # P&L
    pl = requests.get(f"{BASE}/reports/profit-and-loss?from_date=2026-01-01&to_date=2026-12-31", headers=headers).json()
    print(f"\n✓ Profit & Loss:")
    print(f"  Revenue: ${pl.get('total_income', 0):.2f}")
    print(f"  COGS: ${pl.get('total_expense', 0):.2f}")
    print(f"  Net Profit: ${pl.get('net_profit', 0):.2f}")

    db.close()
    db2.close()
    print("\n═══ ALL TESTS PASSED ═══")


if __name__ == "__main__":
    test()
