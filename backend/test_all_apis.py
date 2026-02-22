"""
Comprehensive API Test — Tests EVERY endpoint on localhost:8000
"""
import requests
import json
import sys

BASE = "http://localhost:8000"
RESULTS = []
TOKEN = None
COMPANY_ID = None

# Test data storage
DATA = {}


def test(method, url, expected_status, label, json_data=None, auth=True):
    """Run a single API test."""
    headers = {}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{url}", headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            r = requests.post(f"{BASE}{url}", headers=headers, json=json_data, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            r = requests.put(f"{BASE}{url}", headers=headers, json=json_data, timeout=10)
        
        passed = r.status_code == expected_status
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {method:4s} {url:50s} → {r.status_code} (expected {expected_status}) — {label}")
        
        if not passed:
            try:
                print(f"       Response: {r.text[:200]}")
            except:
                pass
        
        RESULTS.append({"label": label, "passed": passed, "status": r.status_code})
        
        try:
            return r.json() if r.text else {}
        except:
            return {}
    except Exception as e:
        print(f"  ❌ {method:4s} {url:50s} → ERROR: {e} — {label}")
        RESULTS.append({"label": label, "passed": False, "status": "ERROR"})
        return {}


def run_all_tests():
    global TOKEN, COMPANY_ID, DATA

    print("=" * 80)
    print("  COMPREHENSIVE API TEST — Manufacturing ERP Backend")
    print("  Backend: http://localhost:8000")
    print("=" * 80)

    # ═══════════════════════════════════════════════════════════
    print("\n📌 1. DEFAULT ENDPOINTS")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/", 200, "Root endpoint", auth=False)
    test("GET", "/health", 200, "Health check", auth=False)

    # ═══════════════════════════════════════════════════════════
    print("\n🔐 2. AUTHENTICATION")
    # ═══════════════════════════════════════════════════════════
    
    # Login
    resp = test("POST", "/api/auth/login", 200, "Login as admin",
                json_data={"username": "admin", "password": "admin123"}, auth=False)
    TOKEN = resp.get("access_token", "")
    COMPANY_ID = resp.get("user", {}).get("company_id", "")
    
    # Login with wrong password
    test("POST", "/api/auth/login", 401, "Login with wrong password",
         json_data={"username": "admin", "password": "wrong"}, auth=False)
    
    # Get current user
    test("GET", "/api/auth/me", 200, "Get current user (me)")
    
    # Register new user
    resp = test("POST", f"/api/auth/register?company_id={COMPANY_ID}", 201, "Register new user",
                json_data={"username": "testuser", "email": "test@test.com",
                           "password": "test123", "full_name": "Test User", "role": "store_manager"})
    DATA["test_user_id"] = resp.get("id", "")

    # ═══════════════════════════════════════════════════════════
    print("\n📦 3. CATEGORIES")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", "/api/categories", 201, "Create category",
                json_data={"name": "Precious Metals", "description": "Gold, Silver, Platinum"})
    DATA["category_id"] = resp.get("id", "")
    
    test("GET", "/api/categories", 200, "List categories")

    # ═══════════════════════════════════════════════════════════
    print("\n📏 4. UNITS OF MEASURE")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/api/uom", 200, "List UOMs")
    
    resp = test("POST", "/api/uom", 201, "Create custom UOM",
                json_data={"name": "Milligrams", "abbreviation": "mg"})
    DATA["custom_uom_id"] = resp.get("id", "")
    
    # Get existing UOMs for later use
    uoms = requests.get(f"{BASE}/api/uom", headers={"Authorization": f"Bearer {TOKEN}"}).json()
    DATA["uom_g"] = next((u["id"] for u in uoms if u["abbreviation"] == "g"), "")
    DATA["uom_pcs"] = next((u["id"] for u in uoms if u["abbreviation"] == "pcs"), "")
    DATA["uom_kg"] = next((u["id"] for u in uoms if u["abbreviation"] == "kg"), "")
    
    # UOM Conversions
    resp = test("POST", "/api/uom/conversions", 201, "Create UOM conversion (g→kg)",
                json_data={"from_uom_id": DATA["uom_g"], "to_uom_id": DATA["uom_kg"],
                           "conversion_factor": 0.001})
    
    test("GET", "/api/uom/conversions", 200, "List UOM conversions")

    # ═══════════════════════════════════════════════════════════
    print("\n🏭 5. WAREHOUSES")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/api/warehouses", 200, "List warehouses")
    
    resp = test("POST", "/api/warehouses", 201, "Create second warehouse",
                json_data={"name": "Raw Material Store", "code": "WH-RM", "address": "Building B"})
    DATA["wh2_id"] = resp.get("id", "")
    
    # Get main warehouse ID
    warehouses = requests.get(f"{BASE}/api/warehouses", headers={"Authorization": f"Bearer {TOKEN}"}).json()
    DATA["wh_main"] = next((w["id"] for w in warehouses if w["code"] == "WH-MAIN"), "")
    
    test("PUT", f"/api/warehouses/{DATA['wh2_id']}", 200, "Update warehouse",
         json_data={"name": "Raw Material Store (Updated)", "address": "Building B, Floor 2"})
    
    test("GET", f"/api/warehouses/{DATA['wh_main']}/stock", 200, "Get warehouse stock")

    # ═══════════════════════════════════════════════════════════
    print("\n📋 6. ITEMS (ITEM MASTER)")
    # ═══════════════════════════════════════════════════════════
    # Create raw materials
    resp = test("POST", "/api/items", 201, "Create raw material (Silver 925)",
                json_data={"name": "Silver 925", "sku": "SLV-925", "barcode": "8901234567890",
                           "item_type": "raw_material", "uom_id": DATA["uom_g"],
                           "category_id": DATA["category_id"], "base_cost": 2.50, "reorder_level": 100})
    DATA["silver_id"] = resp.get("id", "")
    
    resp = test("POST", "/api/items", 201, "Create raw material (CZ Stone)",
                json_data={"name": "Cubic Zirconia", "sku": "CZ-001",
                           "item_type": "raw_material", "uom_id": DATA["uom_pcs"], "base_cost": 0.50})
    DATA["stone_id"] = resp.get("id", "")
    
    # Create finished good
    resp = test("POST", "/api/items", 201, "Create finished good (Silver Ring)",
                json_data={"name": "Silver Ring 925", "sku": "RING-925",
                           "item_type": "finished_good", "uom_id": DATA["uom_pcs"]})
    DATA["ring_id"] = resp.get("id", "")
    
    # List and filter
    test("GET", "/api/items", 200, "List all items")
    test("GET", "/api/items?item_type=raw_material", 200, "List raw materials only")
    test("GET", "/api/items?item_type=finished_good", 200, "List finished goods only")
    test("GET", f"/api/items/{DATA['silver_id']}", 200, "Get item by ID")
    test("GET", "/api/items/barcode/8901234567890", 200, "Get item by barcode")
    test("GET", "/api/items/barcode/NONEXISTENT", 404, "Get item by invalid barcode")
    
    test("PUT", f"/api/items/{DATA['silver_id']}", 200, "Update item",
         json_data={"description": "Sterling silver 925 grade", "reorder_level": 200})

    # ═══════════════════════════════════════════════════════════
    print("\n📊 7. STOCK LEDGER")
    # ═══════════════════════════════════════════════════════════
    # Record opening stock (via direct service call since there's no POST endpoint for manual entries)
    sys.path.insert(0, "/Users/abdurrafayfarooqui/dev/silver inventory managment/backend")
    from app.database import SessionLocal
    from app.services.stock_ledger_service import StockLedgerService
    db = SessionLocal()
    
    StockLedgerService.record_entry(db, COMPANY_ID, DATA["silver_id"], DATA["wh_main"],
        qty_in=500, qty_out=0, unit_cost=2.50,
        reference_type="opening_balance", reference_id="OPENING",
        description="Opening balance Silver")
    StockLedgerService.record_entry(db, COMPANY_ID, DATA["stone_id"], DATA["wh_main"],
        qty_in=200, qty_out=0, unit_cost=0.50,
        reference_type="opening_balance", reference_id="OPENING",
        description="Opening balance CZ Stones")
    db.commit()
    db.close()
    print("  ✅ Opening stock recorded via service (500g Silver, 200pcs CZ)")
    
    # API endpoints
    test("GET", "/api/stock-ledger/entries", 200, "List stock ledger entries")
    test("GET", f"/api/stock-ledger/entries?item_id={DATA['silver_id']}", 200, "Filter ledger by item")
    test("GET", f"/api/stock-ledger/balance?item_id={DATA['silver_id']}", 200, "Get stock balance")
    test("GET", f"/api/stock-ledger/balance?item_id={DATA['silver_id']}&warehouse_id={DATA['wh_main']}", 200, "Get balance per warehouse")
    test("GET", "/api/stock-ledger/balances", 200, "Get all stock balances")
    test("GET", "/api/stock-ledger/balances?item_type=raw_material", 200, "Get RM balances")

    # ═══════════════════════════════════════════════════════════
    print("\n🔧 8. BILL OF MATERIALS")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", "/api/bom/", 201, "Create BOM v1.0",
                json_data={
                    "product_id": DATA["ring_id"],
                    "version": "v1.0",
                    "is_active": True,
                    "notes": "Standard silver ring",
                    "items": [
                        {"raw_item_id": DATA["silver_id"], "quantity": 10, "wastage_percent": 5},
                        {"raw_item_id": DATA["stone_id"], "quantity": 1, "wastage_percent": 0},
                    ]
                })
    DATA["bom_id"] = resp.get("id", "")
    
    test("GET", "/api/bom/", 200, "List all BOMs")
    test("GET", f"/api/bom/?product_id={DATA['ring_id']}", 200, "List BOMs for product")
    test("GET", f"/api/bom/{DATA['bom_id']}", 200, "Get BOM by ID")
    test("GET", f"/api/bom/{DATA['bom_id']}/requirements?order_qty=10", 200, "Preview BOM requirements")

    # ═══════════════════════════════════════════════════════════
    print("\n🏭 9. PRODUCTION ORDERS")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", "/api/production-orders/", 201, "Create production order (10 rings)",
                json_data={
                    "product_id": DATA["ring_id"],
                    "bom_id": DATA["bom_id"],
                    "order_qty": 10,
                    "warehouse_id": DATA["wh_main"],
                    "notes": "Test batch"
                })
    DATA["po_id"] = resp.get("id", "")
    DATA["po_number"] = resp.get("order_number", "")
    
    test("GET", "/api/production-orders/", 200, "List production orders")
    test("GET", "/api/production-orders/?status=planned", 200, "Filter POs by status")
    test("GET", f"/api/production-orders/{DATA['po_id']}", 200, "Get production order by ID")
    
    # Start production
    test("POST", f"/api/production-orders/{DATA['po_id']}/start", 200, "Start production")
    
    # ═══════════════════════════════════════════════════════════
    print("\n📤 10. WIP ISSUES")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", f"/api/production-orders/{DATA['po_id']}/wip-issues", 201, "Issue materials to WIP",
                json_data={
                    "production_order_id": DATA["po_id"],
                    "issue_date": "2026-02-21",
                    "items": [
                        {"item_id": DATA["silver_id"], "warehouse_id": DATA["wh_main"], "quantity": 105},
                        {"item_id": DATA["stone_id"], "warehouse_id": DATA["wh_main"], "quantity": 10},
                    ]
                })
    DATA["wip_id"] = resp.get("id", "")

    # ═══════════════════════════════════════════════════════════
    print("\n💰 11. PRODUCTION EXPENSES")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", f"/api/production-orders/{DATA['po_id']}/expenses", 201, "Record direct labor expense",
                json_data={
                    "production_order_id": DATA["po_id"],
                    "expense_type": "direct_labor",
                    "amount": 50.00,
                    "expense_date": "2026-02-21",
                    "description": "Ring polishing labor"
                })
    DATA["expense_id"] = resp.get("id", "")
    
    resp = test("POST", f"/api/production-orders/{DATA['po_id']}/expenses", 201, "Record electricity expense",
                json_data={
                    "production_order_id": DATA["po_id"],
                    "expense_type": "electricity",
                    "amount": 15.00,
                    "expense_date": "2026-02-21",
                    "description": "Machine power consumption"
                })

    # ═══════════════════════════════════════════════════════════
    print("\n✅ 12. PRODUCTION COMPLETION")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", f"/api/production-orders/{DATA['po_id']}/complete", 200, "Complete production",
                json_data={"completed_qty": 10, "completion_date": "2026-02-21"})
    
    if resp:
        uc = resp.get("unit_cost", 0)
        mc = resp.get("total_material_cost", 0)
        ex = resp.get("total_expenses", 0)
        print(f"       📊 Material: ${mc:.2f} | Expenses: ${ex:.2f} | Unit Cost: ${uc:.2f}/ring")

    # ═══════════════════════════════════════════════════════════
    print("\n🛒 13. SALES")
    # ═══════════════════════════════════════════════════════════
    resp = test("POST", "/api/sales/", 201, "Create sale (5 rings @ $80)",
                json_data={
                    "customer_name": "Jewelry Store A",
                    "order_date": "2026-02-21",
                    "items": [{
                        "item_id": DATA["ring_id"],
                        "warehouse_id": DATA["wh_main"],
                        "quantity": 5,
                        "unit_price": 80.00,
                    }],
                    "notes": "First sale"
                })
    DATA["sale_id"] = resp.get("id", "")
    
    if resp:
        rev = float(resp.get("total_amount", 0))
        cogs = float(resp.get("total_cost", 0))
        print(f"       📊 Revenue: ${rev:.2f} | COGS: ${cogs:.2f} | Profit: ${rev - cogs:.2f}")
    
    test("GET", "/api/sales/", 200, "List sales orders")
    test("GET", f"/api/sales/{DATA['sale_id']}", 200, "Get sale by ID")

    # ═══════════════════════════════════════════════════════════
    print("\n📒 14. ACCOUNTING")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/api/accounting/accounts", 200, "List chart of accounts")
    test("GET", "/api/accounting/accounts?account_type=asset", 200, "List asset accounts only")
    test("GET", "/api/accounting/accounts?account_type=expense", 200, "List expense accounts only")
    
    test("GET", "/api/accounting/journal-entries", 200, "List journal entries")
    test("GET", "/api/accounting/journal-entries?reference_type=wip_issue", 200, "Filter JEs by WIP issues")
    test("GET", "/api/accounting/journal-entries?reference_type=sale", 200, "Filter JEs by sales")
    
    # Get first JE ID for detail
    jes = requests.get(f"{BASE}/api/accounting/journal-entries", 
                       headers={"Authorization": f"Bearer {TOKEN}"}).json()
    if jes:
        je_id = jes[0]["id"]
        test("GET", f"/api/accounting/journal-entries/{je_id}", 200, "Get journal entry detail")
    
    # Financial reports
    test("GET", "/api/accounting/trial-balance", 200, "Trial Balance")
    test("GET", "/api/accounting/profit-and-loss?from_date=2026-01-01&to_date=2026-12-31", 200, "Profit & Loss")
    test("GET", "/api/accounting/balance-sheet", 200, "Balance Sheet")

    # ═══════════════════════════════════════════════════════════
    print("\n📊 15. REPORTS")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/api/reports/stock-ledger", 200, "Stock Ledger Report")
    test("GET", f"/api/reports/stock-ledger?item_id={DATA['silver_id']}", 200, "Stock Ledger by item")
    test("GET", "/api/reports/inventory-valuation", 200, "Inventory Valuation")
    test("GET", f"/api/reports/production-cost-sheet/{DATA['po_id']}", 200, "Production Cost Sheet")
    test("GET", "/api/reports/wip-summary", 200, "WIP Summary")
    test("GET", "/api/reports/material-consumption", 200, "Material Consumption")
    test("GET", "/api/reports/trial-balance", 200, "Trial Balance (Reports)")
    test("GET", "/api/reports/profit-and-loss?from_date=2026-01-01&to_date=2026-12-31", 200, "P&L (Reports)")
    test("GET", "/api/reports/balance-sheet", 200, "Balance Sheet (Reports)")

    # ═══════════════════════════════════════════════════════════
    print("\n🚫 16. ERROR HANDLING & EDGE CASES")
    # ═══════════════════════════════════════════════════════════
    test("GET", "/api/auth/me", 401, "Unauthorized access (no token)", auth=False)
    test("GET", "/api/items/nonexistent-id", 404, "Get non-existent item")
    test("POST", "/api/production-orders/nonexistent/start", 404, "Start non-existent PO")
    test("POST", f"/api/production-orders/{DATA['po_id']}/start", 400, "Start already completed PO")
    test("POST", f"/api/production-orders/{DATA['po_id']}/complete", 400, "Complete already completed PO",
         json_data={"completed_qty": 1, "completion_date": "2026-02-21"})

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)
    
    print(f"\n  📊 RESULTS: {passed}/{total} passed, {failed} failed")
    
    if failed > 0:
        print("\n  ❌ FAILED TESTS:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"     - {r['label']} (got {r['status']})")
    else:
        print("  🎉 ALL TESTS PASSED!")
    
    print("=" * 80)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
