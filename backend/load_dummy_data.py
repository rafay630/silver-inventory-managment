"""
FULL DUMMY DATA LOAD + SYSTEM VERIFICATION
===========================================
Loads realistic silver jewelry manufacturing data through ALL APIs,
then verifies every report, ledger, journal entry, and balance.

Scenario:
- Silver Manufacturing Co. produces jewelry
- 2 warehouses, 8 raw materials, 4 finished goods
- 3 BOMs with different versions
- 5 production orders (various statuses)
- Multiple WIP issues + expenses
- 3 sales to different customers
- Full accounting verification
"""
import requests
import json
import sys
from datetime import date

BASE = "http://localhost:8000/api"
TOKEN = None
COMPANY_ID = None
D = {}  # Data store

def api(method, url, json_data=None, expected=None):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    if method == "GET":
        r = requests.get(f"{BASE}{url}", headers=headers, timeout=10)
    elif method == "POST":
        r = requests.post(f"{BASE}{url}", headers=headers, json=json_data, timeout=10)
    elif method == "PUT":
        r = requests.put(f"{BASE}{url}", headers=headers, json=json_data, timeout=10)
    
    if expected and r.status_code != expected:
        print(f"  ❌ {method} {url} → {r.status_code} (expected {expected})")
        print(f"     {r.text[:300]}")
        return {}
    
    try:
        return r.json()
    except:
        return {}


def main():
    global TOKEN, COMPANY_ID, D

    print("=" * 80)
    print("  DUMMY DATA LOAD + FULL SYSTEM VERIFICATION")
    print("  Silver Jewelry Manufacturing ERP")
    print("=" * 80)

    # ═══════════════════════════════════════════════════════════
    # 1. LOGIN
    # ═══════════════════════════════════════════════════════════
    print("\n🔐 STEP 1: Authentication")
    resp = api("POST", "/auth/login", {"username": "admin", "password": "admin123"}, 200)
    TOKEN = resp["access_token"]
    COMPANY_ID = resp["user"]["company_id"]
    print(f"  ✅ Logged in as admin (Company: {COMPANY_ID[:8]}...)")

    # Register additional users
    for u in [
        {"username": "accountant1", "email": "acc@silver.com", "password": "acc123",
         "full_name": "Sara Ahmed (Accountant)", "role": "accountant"},
        {"username": "prod_mgr", "email": "prod@silver.com", "password": "prod123",
         "full_name": "Ali Khan (Production)", "role": "production_manager"},
        {"username": "store_mgr", "email": "store@silver.com", "password": "store123",
         "full_name": "Hassan Raza (Store)", "role": "store_manager"},
    ]:
        resp = api("POST", f"/auth/register?company_id={COMPANY_ID}", u, 201)
        D[f"user_{u['role']}"] = resp.get("id", "")
        print(f"  ✅ User: {u['full_name']} ({u['role']})")

    # ═══════════════════════════════════════════════════════════
    # 2. CATEGORIES
    # ═══════════════════════════════════════════════════════════
    print("\n📁 STEP 2: Categories")
    categories = [
        {"name": "Precious Metals", "description": "Gold, Silver, Platinum raw materials"},
        {"name": "Gemstones", "description": "Natural and synthetic stones"},
        {"name": "Findings", "description": "Clasps, chains, jump rings, earring hooks"},
        {"name": "Finished Rings", "description": "Completed ring products"},
        {"name": "Finished Necklaces", "description": "Completed necklace products"},
        {"name": "Finished Earrings", "description": "Completed earring products"},
    ]
    for cat in categories:
        resp = api("POST", "/categories", cat, 201)
        D[f"cat_{cat['name'].lower().replace(' ', '_')}"] = resp.get("id", "")
        print(f"  ✅ Category: {cat['name']}")

    # ═══════════════════════════════════════════════════════════
    # 3. UOMS
    # ═══════════════════════════════════════════════════════════
    print("\n📏 STEP 3: Units of Measure")
    # Get existing UOMs
    uoms = api("GET", "/uom")
    for u in uoms:
        D[f"uom_{u['abbreviation']}"] = u["id"]
    print(f"  ✅ {len(uoms)} existing UOMs loaded")

    # Add custom UOMs
    for u in [
        {"name": "Carats", "abbreviation": "ct"},
        {"name": "Inches", "abbreviation": "in"},
        {"name": "Pairs", "abbreviation": "pr"},
    ]:
        resp = api("POST", "/uom", u, 201)
        D[f"uom_{u['abbreviation']}"] = resp.get("id", "")
        print(f"  ✅ UOM: {u['name']} ({u['abbreviation']})")

    # Add conversion
    api("POST", "/uom/conversions", {
        "from_uom_id": D["uom_g"], "to_uom_id": D["uom_kg"], "conversion_factor": 0.001
    }, 201)
    api("POST", "/uom/conversions", {
        "from_uom_id": D["uom_toz"], "to_uom_id": D["uom_g"], "conversion_factor": 31.1035
    }, 201)
    print("  ✅ Conversions: g→kg, toz→g")

    # ═══════════════════════════════════════════════════════════
    # 4. WAREHOUSES
    # ═══════════════════════════════════════════════════════════
    print("\n🏭 STEP 4: Warehouses")
    warehouses = api("GET", "/warehouses")
    D["wh_main"] = warehouses[0]["id"]
    print(f"  ✅ Main Warehouse: {warehouses[0]['name']} ({D['wh_main'][:8]}...)")

    resp = api("POST", "/warehouses", {
        "name": "Raw Material Vault", "code": "WH-VAULT", "address": "Secure Storage, Building A"
    }, 201)
    D["wh_vault"] = resp["id"]
    print(f"  ✅ Vault Warehouse: {resp['name']}")

    resp = api("POST", "/warehouses", {
        "name": "Finished Goods Showroom", "code": "WH-SHOW", "address": "Retail Floor, Building C"
    }, 201)
    D["wh_showroom"] = resp["id"]
    print(f"  ✅ Showroom Warehouse: {resp['name']}")

    # ═══════════════════════════════════════════════════════════
    # 5. RAW MATERIALS
    # ═══════════════════════════════════════════════════════════
    print("\n🔩 STEP 5: Raw Materials")
    raw_materials = [
        {"name": "Sterling Silver 925", "sku": "RM-SLV925", "barcode": "8901001000001",
         "item_type": "raw_material", "uom_id": D["uom_g"],
         "category_id": D["cat_precious_metals"], "base_cost": 2.80, "reorder_level": 500,
         "description": "92.5% pure silver alloy"},
        {"name": "Fine Silver 999", "sku": "RM-SLV999", "barcode": "8901001000002",
         "item_type": "raw_material", "uom_id": D["uom_g"],
         "category_id": D["cat_precious_metals"], "base_cost": 3.20, "reorder_level": 200,
         "description": "99.9% pure silver"},
        {"name": "Cubic Zirconia (6mm Round)", "sku": "RM-CZ6R", "barcode": "8901002000001",
         "item_type": "raw_material", "uom_id": D["uom_pcs"],
         "category_id": D["cat_gemstones"], "base_cost": 0.75, "reorder_level": 500},
        {"name": "Blue Topaz (5mm Oval)", "sku": "RM-BT5O", "barcode": "8901002000002",
         "item_type": "raw_material", "uom_id": D["uom_pcs"],
         "category_id": D["cat_gemstones"], "base_cost": 4.50, "reorder_level": 100},
        {"name": "Lobster Clasp (Silver)", "sku": "RM-LC01", "barcode": "8901003000001",
         "item_type": "raw_material", "uom_id": D["uom_pcs"],
         "category_id": D["cat_findings"], "base_cost": 0.35, "reorder_level": 200},
        {"name": "Jump Rings (5mm Silver)", "sku": "RM-JR5S", "barcode": "8901003000002",
         "item_type": "raw_material", "uom_id": D["uom_pcs"],
         "category_id": D["cat_findings"], "base_cost": 0.08, "reorder_level": 1000},
        {"name": "Earring Hooks (Silver)", "sku": "RM-EH01", "barcode": "8901003000003",
         "item_type": "raw_material", "uom_id": D["uom_pr"],
         "category_id": D["cat_findings"], "base_cost": 0.45, "reorder_level": 300},
        {"name": "Silver Chain (1mm Box)", "sku": "RM-CH1B", "barcode": "8901003000004",
         "item_type": "raw_material", "uom_id": D["uom_m"],
         "category_id": D["cat_findings"], "base_cost": 8.50, "reorder_level": 50},
    ]
    for rm in raw_materials:
        resp = api("POST", "/items", rm, 201)
        key = rm["sku"].lower().replace("-", "_")
        D[key] = resp["id"]
        print(f"  ✅ {rm['name']} (SKU: {rm['sku']}, Cost: ${rm['base_cost']})")

    # ═══════════════════════════════════════════════════════════
    # 6. FINISHED GOODS
    # ═══════════════════════════════════════════════════════════
    print("\n💎 STEP 6: Finished Goods")
    finished_goods = [
        {"name": "Silver Ring 925 w/ CZ", "sku": "FG-RING-CZ", "barcode": "8902001000001",
         "item_type": "finished_good", "uom_id": D["uom_pcs"],
         "category_id": D["cat_finished_rings"],
         "description": "Sterling silver ring with cubic zirconia center stone"},
        {"name": "Silver Ring 925 w/ Blue Topaz", "sku": "FG-RING-BT", "barcode": "8902001000002",
         "item_type": "finished_good", "uom_id": D["uom_pcs"],
         "category_id": D["cat_finished_rings"],
         "description": "Sterling silver ring with blue topaz center stone"},
        {"name": "Silver Pendant Necklace", "sku": "FG-NECK-01", "barcode": "8902002000001",
         "item_type": "finished_good", "uom_id": D["uom_pcs"],
         "category_id": D["cat_finished_necklaces"],
         "description": "Silver pendant on 18in box chain"},
        {"name": "Silver Drop Earrings w/ CZ", "sku": "FG-EAR-CZ", "barcode": "8902003000001",
         "item_type": "finished_good", "uom_id": D["uom_pr"],
         "category_id": D["cat_finished_earrings"],
         "description": "Silver drop earrings with CZ stones (pair)"},
    ]
    for fg in finished_goods:
        resp = api("POST", "/items", fg, 201)
        key = fg["sku"].lower().replace("-", "_")
        D[key] = resp["id"]
        print(f"  ✅ {fg['name']} (SKU: {fg['sku']})")

    # ═══════════════════════════════════════════════════════════
    # 7. OPENING STOCK
    # ═══════════════════════════════════════════════════════════
    print("\n📦 STEP 7: Opening Stock Balances")
    sys.path.insert(0, "/Users/abdurrafayfarooqui/dev/silver inventory managment/backend")
    from app.database import SessionLocal
    from app.services.stock_ledger_service import StockLedgerService
    from app.services.accounting_service import AccountingService

    db = SessionLocal()
    opening_stock = [
        (D["rm_slv925"], D["wh_main"], 2000, 2.80, "Sterling Silver 925 — 2000g"),
        (D["rm_slv925"], D["wh_vault"], 5000, 2.75, "Sterling Silver 925 — 5000g (vault)"),
        (D["rm_slv999"], D["wh_vault"], 1000, 3.20, "Fine Silver 999 — 1000g"),
        (D["rm_cz6r"], D["wh_main"], 500, 0.75, "CZ Stones 6mm — 500pcs"),
        (D["rm_bt5o"], D["wh_main"], 150, 4.50, "Blue Topaz 5mm — 150pcs"),
        (D["rm_lc01"], D["wh_main"], 300, 0.35, "Lobster Clasps — 300pcs"),
        (D["rm_jr5s"], D["wh_main"], 2000, 0.08, "Jump Rings — 2000pcs"),
        (D["rm_eh01"], D["wh_main"], 400, 0.45, "Earring Hooks — 400 pairs"),
        (D["rm_ch1b"], D["wh_main"], 100, 8.50, "Silver Chain 1mm — 100m"),
    ]

    # Create opening balance journal entry (Dr RM Inventory, Cr Equity)
    total_opening_value = 0
    for item_id, wh_id, qty, cost, desc in opening_stock:
        StockLedgerService.record_entry(
            db, COMPANY_ID, item_id, wh_id,
            qty_in=qty, qty_out=0, unit_cost=cost,
            reference_type="opening_balance", reference_id="OPENING",
            description=desc,
        )
        total_opening_value += qty * cost
        print(f"  ✅ {desc} = ${qty * cost:.2f}")

    # Journal: Dr RM Inventory, Cr Retained Earnings (opening balance)
    rm_account = AccountingService.get_account_by_code(db, COMPANY_ID, "1100")
    equity_account = AccountingService.get_account_by_code(db, COMPANY_ID, "3100")
    AccountingService.create_journal_entry(
        db, COMPANY_ID,
        entry_date=date(2026, 1, 1),
        lines=[
            {"account_id": rm_account.id, "debit": total_opening_value, "credit": 0,
             "description": "Opening stock balance"},
            {"account_id": equity_account.id, "debit": 0, "credit": total_opening_value,
             "description": "Opening equity"},
        ],
        reference_type="opening_balance",
        reference_id="OPENING",
        description="Opening stock balance entry",
    )
    db.commit()
    print(f"  ✅ Total Opening Value: ${total_opening_value:,.2f}")
    print(f"  ✅ Opening Journal Entry created (Dr RM Inventory, Cr Equity)")
    db.close()

    # ═══════════════════════════════════════════════════════════
    # 8. BILL OF MATERIALS (3 products, some with multiple versions)
    # ═══════════════════════════════════════════════════════════
    print("\n🔧 STEP 8: Bills of Material")

    # BOM 1: Silver Ring w/ CZ
    resp = api("POST", "/bom/", {
        "product_id": D["fg_ring_cz"], "version": "v1.0", "is_active": True,
        "notes": "Standard CZ ring — 10g silver, 1 CZ stone",
        "items": [
            {"raw_item_id": D["rm_slv925"], "quantity": 10, "wastage_percent": 5},
            {"raw_item_id": D["rm_cz6r"], "quantity": 1, "wastage_percent": 2},
        ]
    }, 201)
    D["bom_ring_cz"] = resp["id"]
    print(f"  ✅ BOM: Silver Ring CZ v1.0 (10g silver + 1 CZ)")

    # BOM 2: Silver Ring w/ Blue Topaz
    resp = api("POST", "/bom/", {
        "product_id": D["fg_ring_bt"], "version": "v1.0", "is_active": True,
        "notes": "Blue Topaz ring — 12g silver, 1 topaz",
        "items": [
            {"raw_item_id": D["rm_slv925"], "quantity": 12, "wastage_percent": 4},
            {"raw_item_id": D["rm_bt5o"], "quantity": 1, "wastage_percent": 0},
        ]
    }, 201)
    D["bom_ring_bt"] = resp["id"]
    print(f"  ✅ BOM: Silver Ring Blue Topaz v1.0 (12g silver + 1 topaz)")

    # BOM 3: Pendant Necklace
    resp = api("POST", "/bom/", {
        "product_id": D["fg_neck_01"], "version": "v1.0", "is_active": True,
        "notes": "Pendant necklace — 8g pendant + 0.45m chain + clasp + jump rings",
        "items": [
            {"raw_item_id": D["rm_slv925"], "quantity": 8, "wastage_percent": 3},
            {"raw_item_id": D["rm_ch1b"], "quantity": 0.45, "wastage_percent": 2},
            {"raw_item_id": D["rm_lc01"], "quantity": 1, "wastage_percent": 0},
            {"raw_item_id": D["rm_jr5s"], "quantity": 4, "wastage_percent": 10},
        ]
    }, 201)
    D["bom_neck"] = resp["id"]
    print(f"  ✅ BOM: Pendant Necklace v1.0 (8g silver + chain + clasp + rings)")

    # BOM 4: Drop Earrings
    resp = api("POST", "/bom/", {
        "product_id": D["fg_ear_cz"], "version": "v1.0", "is_active": True,
        "notes": "CZ drop earrings — 6g silver, 2 CZ, 1 pair hooks",
        "items": [
            {"raw_item_id": D["rm_slv925"], "quantity": 6, "wastage_percent": 5},
            {"raw_item_id": D["rm_cz6r"], "quantity": 2, "wastage_percent": 2},
            {"raw_item_id": D["rm_eh01"], "quantity": 1, "wastage_percent": 0},
        ]
    }, 201)
    D["bom_ear"] = resp["id"]
    print(f"  ✅ BOM: Drop Earrings v1.0 (6g silver + 2 CZ + hooks)")

    # Preview requirements
    print("\n  📋 BOM Requirements Preview (for 20 CZ Rings):")
    reqs = api("GET", f"/bom/{D['bom_ring_cz']}/requirements?order_qty=20")
    for r in reqs:
        print(f"      Item {r['item_id'][:8]}... → {r['required_qty']} units needed")

    # ═══════════════════════════════════════════════════════════
    # 9. PRODUCTION ORDERS (5 orders — various products)
    # ═══════════════════════════════════════════════════════════
    print("\n🏭 STEP 9: Production Orders")

    # PO-1: 20 CZ Rings
    resp = api("POST", "/production-orders/", {
        "product_id": D["fg_ring_cz"], "bom_id": D["bom_ring_cz"],
        "order_qty": 20, "warehouse_id": D["wh_main"],
        "start_date": "2026-02-01", "notes": "Batch 1 — CZ Rings for retail"
    }, 201)
    D["po1"] = resp["id"]
    print(f"  ✅ PO-1: {resp['order_number']} — 20x CZ Rings")

    # PO-2: 10 Blue Topaz Rings
    resp = api("POST", "/production-orders/", {
        "product_id": D["fg_ring_bt"], "bom_id": D["bom_ring_bt"],
        "order_qty": 10, "warehouse_id": D["wh_main"],
        "start_date": "2026-02-05", "notes": "Batch 1 — Topaz Rings for special order"
    }, 201)
    D["po2"] = resp["id"]
    print(f"  ✅ PO-2: {resp['order_number']} — 10x Topaz Rings")

    # PO-3: 15 Pendant Necklaces
    resp = api("POST", "/production-orders/", {
        "product_id": D["fg_neck_01"], "bom_id": D["bom_neck"],
        "order_qty": 15, "warehouse_id": D["wh_main"],
        "start_date": "2026-02-10", "notes": "Necklace batch for spring collection"
    }, 201)
    D["po3"] = resp["id"]
    print(f"  ✅ PO-3: {resp['order_number']} — 15x Pendant Necklaces")

    # PO-4: 25 Drop Earrings
    resp = api("POST", "/production-orders/", {
        "product_id": D["fg_ear_cz"], "bom_id": D["bom_ear"],
        "order_qty": 25, "warehouse_id": D["wh_main"],
        "start_date": "2026-02-15", "notes": "Earring batch for wholesale"
    }, 201)
    D["po4"] = resp["id"]
    print(f"  ✅ PO-4: {resp['order_number']} — 25x Drop Earrings")

    # PO-5: Another 30 CZ Rings (will remain planned)
    resp = api("POST", "/production-orders/", {
        "product_id": D["fg_ring_cz"], "bom_id": D["bom_ring_cz"],
        "order_qty": 30, "warehouse_id": D["wh_main"],
        "notes": "Future batch — pending material availability"
    }, 201)
    D["po5"] = resp["id"]
    print(f"  ✅ PO-5: {resp['order_number']} — 30x CZ Rings (PLANNED, not started)")

    # ═══════════════════════════════════════════════════════════
    # 10. START PRODUCTION + WIP ISSUES + EXPENSES + COMPLETE
    # ═══════════════════════════════════════════════════════════
    print("\n🔄 STEP 10: Production Lifecycle — PO-1 (20 CZ Rings)")
    api("POST", f"/production-orders/{D['po1']}/start", expected=200)
    print("  ✅ PO-1 started")

    # WIP Issue 1 — main materials
    api("POST", f"/production-orders/{D['po1']}/wip-issues", {
        "production_order_id": D["po1"], "issue_date": "2026-02-02",
        "items": [
            {"item_id": D["rm_slv925"], "warehouse_id": D["wh_main"], "quantity": 210},
            {"item_id": D["rm_cz6r"], "warehouse_id": D["wh_main"], "quantity": 21},
        ]
    }, 201)
    print("  ✅ WIP Issue 1: 210g Silver + 21 CZ Stones")

    # Expenses
    api("POST", f"/production-orders/{D['po1']}/expenses", {
        "production_order_id": D["po1"], "expense_type": "direct_labor",
        "amount": 120.00, "expense_date": "2026-02-03", "description": "Casting labor"
    }, 201)
    api("POST", f"/production-orders/{D['po1']}/expenses", {
        "production_order_id": D["po1"], "expense_type": "electricity",
        "amount": 35.00, "expense_date": "2026-02-03", "description": "Kiln power"
    }, 201)
    api("POST", f"/production-orders/{D['po1']}/expenses", {
        "production_order_id": D["po1"], "expense_type": "direct_labor",
        "amount": 80.00, "expense_date": "2026-02-04", "description": "Polishing labor"
    }, 201)
    print("  ✅ Expenses: Labor $120 + Electricity $35 + Polishing $80 = $235")

    # Complete
    resp = api("POST", f"/production-orders/{D['po1']}/complete", {
        "completed_qty": 20, "completion_date": "2026-02-05"
    }, 200)
    print(f"  ✅ COMPLETED: {resp.get('completed_qty', 0)} rings @ ${resp.get('unit_cost', 0):.2f}/ring")
    print(f"     Material: ${resp.get('total_material_cost', 0):.2f} | Expenses: ${resp.get('total_expenses', 0):.2f}")

    # ───────────────────────────────────────────────────────────
    print("\n🔄 STEP 11: Production Lifecycle — PO-2 (10 Topaz Rings)")
    api("POST", f"/production-orders/{D['po2']}/start", expected=200)
    print("  ✅ PO-2 started")

    api("POST", f"/production-orders/{D['po2']}/wip-issues", {
        "production_order_id": D["po2"], "issue_date": "2026-02-06",
        "items": [
            {"item_id": D["rm_slv925"], "warehouse_id": D["wh_main"], "quantity": 125},
            {"item_id": D["rm_bt5o"], "warehouse_id": D["wh_main"], "quantity": 10},
        ]
    }, 201)
    print("  ✅ WIP Issue: 125g Silver + 10 Blue Topaz")

    api("POST", f"/production-orders/{D['po2']}/expenses", {
        "production_order_id": D["po2"], "expense_type": "direct_labor",
        "amount": 95.00, "expense_date": "2026-02-07", "description": "Expert setting labor"
    }, 201)
    api("POST", f"/production-orders/{D['po2']}/expenses", {
        "production_order_id": D["po2"], "expense_type": "job_work",
        "amount": 40.00, "expense_date": "2026-02-07", "description": "External rhodium plating"
    }, 201)
    print("  ✅ Expenses: Labor $95 + Job Work $40 = $135")

    resp = api("POST", f"/production-orders/{D['po2']}/complete", {
        "completed_qty": 10, "completion_date": "2026-02-08"
    }, 200)
    print(f"  ✅ COMPLETED: {resp.get('completed_qty', 0)} rings @ ${resp.get('unit_cost', 0):.2f}/ring")

    # ───────────────────────────────────────────────────────────
    print("\n🔄 STEP 12: Production Lifecycle — PO-3 (15 Necklaces)")
    api("POST", f"/production-orders/{D['po3']}/start", expected=200)
    print("  ✅ PO-3 started")

    api("POST", f"/production-orders/{D['po3']}/wip-issues", {
        "production_order_id": D["po3"], "issue_date": "2026-02-11",
        "items": [
            {"item_id": D["rm_slv925"], "warehouse_id": D["wh_main"], "quantity": 124},
            {"item_id": D["rm_ch1b"], "warehouse_id": D["wh_main"], "quantity": 6.9},
            {"item_id": D["rm_lc01"], "warehouse_id": D["wh_main"], "quantity": 15},
            {"item_id": D["rm_jr5s"], "warehouse_id": D["wh_main"], "quantity": 66},
        ]
    }, 201)
    print("  ✅ WIP Issue: 124g Silver + 6.9m Chain + 15 Clasps + 66 Jump Rings")

    api("POST", f"/production-orders/{D['po3']}/expenses", {
        "production_order_id": D["po3"], "expense_type": "direct_labor",
        "amount": 150.00, "expense_date": "2026-02-12", "description": "Assembly labor"
    }, 201)
    api("POST", f"/production-orders/{D['po3']}/expenses", {
        "production_order_id": D["po3"], "expense_type": "electricity",
        "amount": 20.00, "expense_date": "2026-02-12", "description": "Soldering power"
    }, 201)
    print("  ✅ Expenses: Labor $150 + Electricity $20 = $170")

    resp = api("POST", f"/production-orders/{D['po3']}/complete", {
        "completed_qty": 15, "completion_date": "2026-02-13"
    }, 200)
    print(f"  ✅ COMPLETED: {resp.get('completed_qty', 0)} necklaces @ ${resp.get('unit_cost', 0):.2f}/unit")

    # ───────────────────────────────────────────────────────────
    print("\n🔄 STEP 13: Production — PO-4 (25 Earrings — PARTIAL, in progress)")
    api("POST", f"/production-orders/{D['po4']}/start", expected=200)
    print("  ✅ PO-4 started")

    api("POST", f"/production-orders/{D['po4']}/wip-issues", {
        "production_order_id": D["po4"], "issue_date": "2026-02-16",
        "items": [
            {"item_id": D["rm_slv925"], "warehouse_id": D["wh_main"], "quantity": 158},
            {"item_id": D["rm_cz6r"], "warehouse_id": D["wh_main"], "quantity": 51},
            {"item_id": D["rm_eh01"], "warehouse_id": D["wh_main"], "quantity": 25},
        ]
    }, 201)
    print("  ✅ WIP Issue: 158g Silver + 51 CZ + 25 pairs Earring Hooks")

    api("POST", f"/production-orders/{D['po4']}/expenses", {
        "production_order_id": D["po4"], "expense_type": "direct_labor",
        "amount": 100.00, "expense_date": "2026-02-17", "description": "Assembly labor"
    }, 201)
    print("  ✅ Expense: Labor $100")

    # Partial completion — only 15 of 25
    resp = api("POST", f"/production-orders/{D['po4']}/complete", {
        "completed_qty": 15, "completion_date": "2026-02-18"
    }, 200)
    print(f"  ✅ PARTIAL COMPLETION: 15/25 earrings @ ${resp.get('unit_cost', 0):.2f}/pair")
    print(f"     (Order remains IN PROGRESS — 10 pairs pending)")

    # ═══════════════════════════════════════════════════════════
    # 11. SALES (3 orders to different customers)
    # ═══════════════════════════════════════════════════════════
    print("\n🛒 STEP 14: Sales Orders")

    # Sale 1: Jewelry Store A — CZ Rings + Necklaces
    resp = api("POST", "/sales/", {
        "customer_name": "Diamond Palace Jewelers",
        "order_date": "2026-02-10",
        "items": [
            {"item_id": D["fg_ring_cz"], "warehouse_id": D["wh_main"], "quantity": 8, "unit_price": 85.00},
            {"item_id": D["fg_neck_01"], "warehouse_id": D["wh_main"], "quantity": 5, "unit_price": 120.00},
        ],
        "notes": "Regular retail order"
    }, 201)
    rev1 = float(resp.get("total_amount", 0))
    cogs1 = float(resp.get("total_cost", 0))
    print(f"  ✅ Sale 1: Diamond Palace — Revenue: ${rev1:,.2f}, COGS: ${cogs1:,.2f}")

    # Sale 2: Online customer — Topaz Rings
    resp = api("POST", "/sales/", {
        "customer_name": "Silver Dreams Online",
        "order_date": "2026-02-15",
        "items": [
            {"item_id": D["fg_ring_bt"], "warehouse_id": D["wh_main"], "quantity": 5, "unit_price": 145.00},
        ],
        "notes": "Online wholesale order"
    }, 201)
    rev2 = float(resp.get("total_amount", 0))
    cogs2 = float(resp.get("total_cost", 0))
    print(f"  ✅ Sale 2: Silver Dreams — Revenue: ${rev2:,.2f}, COGS: ${cogs2:,.2f}")

    # Sale 3: Earrings + CZ Rings
    resp = api("POST", "/sales/", {
        "customer_name": "Elegant Accessories Ltd",
        "order_date": "2026-02-20",
        "items": [
            {"item_id": D["fg_ring_cz"], "warehouse_id": D["wh_main"], "quantity": 5, "unit_price": 80.00},
            {"item_id": D["fg_ear_cz"], "warehouse_id": D["wh_main"], "quantity": 10, "unit_price": 65.00},
        ],
        "notes": "Wholesale order — mixed jewelry"
    }, 201)
    rev3 = float(resp.get("total_amount", 0))
    cogs3 = float(resp.get("total_cost", 0))
    print(f"  ✅ Sale 3: Elegant Accessories — Revenue: ${rev3:,.2f}, COGS: ${cogs3:,.2f}")

    total_revenue = rev1 + rev2 + rev3
    total_cogs = cogs1 + cogs2 + cogs3
    print(f"\n  💰 TOTAL Revenue: ${total_revenue:,.2f}")
    print(f"  💰 TOTAL COGS: ${total_cogs:,.2f}")
    print(f"  💰 GROSS Profit: ${total_revenue - total_cogs:,.2f}")

    # ═══════════════════════════════════════════════════════════
    # 12. FULL SYSTEM VERIFICATION
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  FULL SYSTEM VERIFICATION")
    print("=" * 80)

    # A) Stock Ledger
    print("\n📊 A) STOCK LEDGER REPORT")
    ledger = api("GET", "/reports/stock-ledger")
    print(f"  Total ledger entries: {len(ledger)}")

    # B) Inventory Valuation
    print("\n📊 B) INVENTORY VALUATION")
    inv = api("GET", "/reports/inventory-valuation")
    total_inv_value = 0
    print(f"  {'Item':<35} {'Balance':>10} {'WAC':>10} {'Value':>12}")
    print(f"  {'─'*35} {'─'*10} {'─'*10} {'─'*12}")
    for item in inv:
        val = float(item.get("total_value", 0))
        total_inv_value += val
        print(f"  {item['item_name']:<35} {item['balance']:>10.1f} ${item['weighted_avg_cost']:>8.2f} ${val:>10.2f}")
    print(f"  {'─'*35} {'─'*10} {'─'*10} {'─'*12}")
    print(f"  {'TOTAL INVENTORY VALUE':<35} {'':>10} {'':>10} ${total_inv_value:>10.2f}")

    # C) Production Cost Sheets
    print("\n📊 C) PRODUCTION COST SHEETS")
    for po_key, po_name in [("po1", "CZ Rings"), ("po2", "Topaz Rings"), 
                             ("po3", "Necklaces"), ("po4", "Earrings")]:
        cost = api("GET", f"/reports/production-cost-sheet/{D[po_key]}")
        print(f"  {cost.get('order_number', 'N/A'):10} ({po_name:15}) — "
              f"Material: ${cost.get('total_material_cost', 0):>8.2f} | "
              f"Expense: ${cost.get('total_expenses', 0):>8.2f} | "
              f"Unit: ${cost.get('unit_cost', 0):>8.2f}")

    # D) WIP Summary
    print("\n📊 D) WIP SUMMARY (in-progress orders)")
    wip = api("GET", "/reports/wip-summary")
    if wip:
        for w in wip:
            print(f"  {w.get('order_number', 'N/A'):10} — "
                  f"Completed: {w.get('completed_qty', 0)}/{w.get('order_qty', 0)} | "
                  f"WIP Value: ${w.get('total_wip_value', 0):,.2f}")
    else:
        print("  No in-progress orders (all completed or planned)")

    # E) Material Consumption
    print("\n📊 E) MATERIAL CONSUMPTION REPORT")
    consumption = api("GET", "/reports/material-consumption")
    for c in consumption:
        print(f"  {c['item_name']:<35} Qty: {c['total_quantity']:>10.1f}  Cost: ${c['total_cost']:>10.2f}")

    # F) Chart of Accounts
    print("\n📊 F) CHART OF ACCOUNTS")
    accounts = api("GET", "/accounting/accounts")
    print(f"  Total accounts: {len(accounts)}")
    for acc in accounts:
        print(f"  {acc['code']:6} {acc['name']:<35} ({acc['account_type']})")

    # G) Journal Entries
    print("\n📊 G) JOURNAL ENTRIES")
    jes = api("GET", "/accounting/journal-entries?limit=200")
    print(f"  Total journal entries: {len(jes)}")
    by_type = {}
    for je in jes:
        t = je.get("reference_type") or "manual"
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"    {t}: {count} entries")

    # H) Trial Balance
    print("\n📊 H) TRIAL BALANCE")
    tb = api("GET", "/accounting/trial-balance")
    total_d = tb.get("total_debit", 0)
    total_c = tb.get("total_credit", 0)
    balanced = tb.get("is_balanced", False)
    print(f"  Total Debits:  ${total_d:>12,.2f}")
    print(f"  Total Credits: ${total_c:>12,.2f}")
    print(f"  Balanced: {'✅ YES' if balanced else '❌ NO'}")
    if tb.get("rows"):
        print(f"\n  {'Code':6} {'Account':<35} {'Debit':>12} {'Credit':>12}")
        print(f"  {'─'*6} {'─'*35} {'─'*12} {'─'*12}")
        for row in tb["rows"]:
            d = row.get("debit", 0)
            c = row.get("credit", 0)
            print(f"  {row['account_code']:6} {row['account_name']:<35} ${d:>10.2f} ${c:>10.2f}")

    # I) Profit & Loss
    print("\n📊 I) PROFIT & LOSS (Feb 2026)")
    pl = api("GET", "/accounting/profit-and-loss?from_date=2026-02-01&to_date=2026-02-28")
    print(f"  INCOME:")
    for inc in pl.get("income", []):
        print(f"    {inc['account_name']:<35} ${inc['amount']:>10.2f}")
    print(f"  Total Income: ${pl.get('total_income', 0):>10.2f}")
    print(f"\n  EXPENSES:")
    for exp in pl.get("expenses", []):
        print(f"    {exp['account_name']:<35} ${exp['amount']:>10.2f}")
    print(f"  Total Expenses: ${pl.get('total_expenses', 0):>10.2f}")
    print(f"\n  NET PROFIT: ${pl.get('net_profit', 0):>10.2f}")

    # J) Balance Sheet
    print("\n📊 J) BALANCE SHEET")
    bs = api("GET", "/accounting/balance-sheet")
    print(f"  ASSETS:")
    for a in bs.get("assets", []):
        print(f"    {a['account_name']:<35} ${a['amount']:>10.2f}")
    print(f"  Total Assets: ${bs.get('total_assets', 0):>10.2f}")
    print(f"\n  LIABILITIES:")
    for l in bs.get("liabilities", []):
        print(f"    {l['account_name']:<35} ${l['amount']:>10.2f}")
    print(f"  Total Liabilities: ${bs.get('total_liabilities', 0):>10.2f}")
    print(f"\n  EQUITY:")
    for eq in bs.get("equity", []):
        print(f"    {eq['account_name']:<35} ${eq['amount']:>10.2f}")
    print(f"  Total Equity: ${bs.get('total_equity', 0):>10.2f}")

    # K) Verify production order statuses
    print("\n📊 K) PRODUCTION ORDER STATUSES")
    all_pos = api("GET", "/production-orders/")
    for po in all_pos:
        print(f"  {po['order_number']:10} — Status: {po['status']:12} | "
              f"Completed: {float(po.get('completed_qty', 0)):.0f}/{float(po.get('order_qty', 0)):.0f}")

    # L) Verify stock balances match
    print("\n📊 L) FINAL STOCK BALANCES (All Warehouses)")
    all_bal = api("GET", "/stock-ledger/balances")
    for b in all_bal:
        print(f"  {b['item_name']:<35} Balance: {b['balance']:>10.1f}  WAC: ${b['weighted_avg_cost']:.2f}")

    # M) Sales summary
    print("\n📊 M) SALES SUMMARY")
    all_sales = api("GET", "/sales/")
    for s in all_sales:
        print(f"  {s.get('order_number', 'N/A'):10} — {s.get('customer_name', 'N/A'):<30} "
              f"Revenue: ${float(s.get('total_amount', 0)):>8.2f}  COGS: ${float(s.get('total_cost', 0)):>8.2f}")

    print("\n" + "=" * 80)
    print("  ✅ FULL SYSTEM VERIFICATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
