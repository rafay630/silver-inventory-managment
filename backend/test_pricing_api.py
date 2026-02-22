"""Test all Product Pricing / Sales Catalog API endpoints."""
import requests
import sys

BASE = 'http://localhost:8000/api'
passed = 0
failed = 0


def test(method, url, data=None, expected=200, desc='', headers=None):
    global passed, failed
    h = headers or {}
    if method == 'GET':
        r = requests.get(f'{BASE}{url}', headers=h, timeout=5)
    elif method == 'POST':
        r = requests.post(f'{BASE}{url}', headers=h, json=data, timeout=5)
    ok = r.status_code == expected
    if ok:
        passed += 1
        mark = '✅'
    else:
        failed += 1
        mark = '❌'
    print(f'  {mark} {method:4} {url:<50} → {r.status_code} ({desc})')
    if not ok:
        print(f'     Body: {r.text[:200]}')
    try:
        return r.json()
    except:
        return {}


def main():
    global passed, failed

    print('=' * 60)
    print('  SALES CATALOG / PRICING API TESTS')
    print('=' * 60)

    # Login
    print('\n🔐 AUTH')
    resp = test('POST', '/auth/login', {'username': 'admin', 'password': 'admin123'}, 200, 'Login')
    TOKEN = resp['access_token']
    H = {'Authorization': f'Bearer {TOKEN}'}

    # Create 2 finished goods + opening stock
    print('\n📦 SETUP — Items + Stock')
    uoms = requests.get(f'{BASE}/uom', headers=H).json()
    uom_pcs = next(u['id'] for u in uoms if u['abbreviation'] == 'pcs')
    whs = requests.get(f'{BASE}/warehouses', headers=H).json()
    wh_id = whs[0]['id']

    fg1 = test('POST', '/items', {
        'name': 'Silver Ring CZ', 'sku': 'FG-R1',
        'item_type': 'finished_good', 'uom_id': uom_pcs, 'base_cost': 30.0
    }, 201, 'Create FG-1', H)

    fg2 = test('POST', '/items', {
        'name': 'Silver Necklace', 'sku': 'FG-N1',
        'item_type': 'finished_good', 'uom_id': uom_pcs, 'base_cost': 50.0
    }, 201, 'Create FG-2', H)

    # Record opening stock
    sys.path.insert(0, '.')
    from app.database import SessionLocal
    from app.services.stock_ledger_service import StockLedgerService
    db = SessionLocal()
    company_id = requests.get(f'{BASE}/auth/me', headers=H).json()['company_id']
    StockLedgerService.record_entry(db, company_id, fg1['id'], wh_id,
                                     qty_in=50, qty_out=0, unit_cost=30.0,
                                     reference_type='opening', reference_id='OPEN',
                                     description='FG1 opening')
    StockLedgerService.record_entry(db, company_id, fg2['id'], wh_id,
                                     qty_in=20, qty_out=0, unit_cost=50.0,
                                     reference_type='opening', reference_id='OPEN',
                                     description='FG2 opening')
    db.commit()
    db.close()
    print('  ✅ Opening stock recorded (50 rings, 20 necklaces)')

    # 1. Get catalog
    print('\n📋 PRICING CATALOG')
    catalog = test('GET', '/pricing/catalog', expected=200, desc='Full catalog', headers=H)
    assert len(catalog) == 2, f'Expected 2 items, got {len(catalog)}'
    assert catalog[0]['status'] == 'draft'
    print(f'     {len(catalog)} items, both draft')
    for c in catalog:
        print(f'     {c["item_name"]}: WAC=${c["current_wac"]}, stock={c["current_stock"]}, status={c["status"]}')

    # 2. Set margin for FG-1 (30%)
    print('\n💰 SET MARGIN')
    pricing1 = test('POST', '/pricing/', {
        'item_id': fg1['id'], 'profit_margin_percent': 30.0
    }, 201, 'Set 30% margin on Ring', H)
    print(f'     cost_basis={pricing1["cost_basis"]}, selling_price={pricing1["selling_price"]}, status={pricing1["status"]}')
    assert pricing1['selling_price'] == 39.0, f'Expected 39.0, got {pricing1["selling_price"]}'
    assert pricing1['status'] == 'draft'
    print('     30% margin: $30 WAC → $39.00 selling price ✓')

    # 3. Set margin for FG-2 (50%)
    pricing2 = test('POST', '/pricing/', {
        'item_id': fg2['id'], 'profit_margin_percent': 50.0
    }, 201, 'Set 50% margin on Necklace', H)
    assert pricing2['selling_price'] == 75.0
    print(f'     50% margin: $50 WAC → $75.00 selling price ✓')

    # 4. Listed items — should be empty
    print('\n📋 LISTED ITEMS (should be empty)')
    listed = test('GET', '/pricing/listed', expected=200, desc='Listed items (empty)', headers=H)
    assert len(listed) == 0
    print('     0 listed items (both still draft) ✓')

    # 5. Publish FG-1
    print('\n🟢 PUBLISH')
    pub = test('POST', f'/pricing/{pricing1["id"]}/publish', expected=200, desc='Publish Ring', headers=H)
    assert pub['status'] == 'listed'
    print(f'     Ring published: status={pub["status"]}, price=${pub["selling_price"]} ✓')

    # 6. Listed items — should have 1
    listed = test('GET', '/pricing/listed', expected=200, desc='Listed items (1)', headers=H)
    assert len(listed) == 1
    assert listed[0]['item_name'] == 'Silver Ring CZ'
    print(f'     1 listed item: {listed[0]["item_name"]} @ ${listed[0]["selling_price"]} ✓')

    # 7. Publish FG-2
    pub2 = test('POST', f'/pricing/{pricing2["id"]}/publish', expected=200, desc='Publish Necklace', headers=H)
    assert pub2['status'] == 'listed'
    listed = test('GET', '/pricing/listed', expected=200, desc='Listed items (2)', headers=H)
    assert len(listed) == 2
    print(f'     2 listed items ✓')

    # 8. Unpublish FG-2
    print('\n🔴 UNPUBLISH')
    unpub = test('POST', f'/pricing/{pricing2["id"]}/unpublish', expected=200, desc='Unpublish Necklace', headers=H)
    assert unpub['status'] == 'draft'
    listed = test('GET', '/pricing/listed', expected=200, desc='Listed items (back to 1)', headers=H)
    assert len(listed) == 1
    print('     Necklace unpublished, 1 listed item remaining ✓')

    # 9. Update margin
    print('\n✏️  UPDATE MARGIN')
    p1_updated = test('POST', '/pricing/', {
        'item_id': fg1['id'], 'profit_margin_percent': 40.0, 'notes': 'Updated for spring'
    }, 201, 'Update margin to 40%', H)
    assert p1_updated['selling_price'] == 42.0
    print(f'     New selling_price: ${p1_updated["selling_price"]} (40% of $30 = $42) ✓')

    # 10. Edge cases
    print('\n🚫 EDGE CASES')
    test('POST', '/pricing/', {
        'item_id': 'nonexistent-id', 'profit_margin_percent': 30.0
    }, 404, 'Non-existent item', H)
    test('POST', '/pricing/', {
        'item_id': fg1['id'], 'profit_margin_percent': 600.0
    }, 400, 'Margin > 500%', H)
    test('POST', '/pricing/nonexistent/publish', expected=404, desc='Publish non-existent', headers=H)

    # 11. Non-admin cannot set pricing
    print('\n🔒 ROLE CHECK')
    # Register a non-admin user
    reg = test('POST', f'/auth/register?company_id={company_id}', {
        'username': 'viewer1', 'email': 'view@test.com',
        'password': 'view123', 'full_name': 'Viewer', 'role': 'store_manager'
    }, 201, 'Register store_manager', H)
    # Login as store_manager
    login2 = test('POST', '/auth/login', {'username': 'viewer1', 'password': 'view123'}, 200, 'Login as store_manager')
    H2 = {'Authorization': f'Bearer {login2["access_token"]}'}
    # Can view catalog
    test('GET', '/pricing/catalog', expected=200, desc='Store mgr can view catalog', headers=H2)
    # Cannot set pricing
    test('POST', '/pricing/', {
        'item_id': fg1['id'], 'profit_margin_percent': 20.0
    }, 403, 'Store mgr cannot set pricing', H2)
    # Cannot publish
    test('POST', f'/pricing/{pricing1["id"]}/publish', expected=403, desc='Store mgr cannot publish', headers=H2)

    # 12. Final catalog state
    print('\n📋 FINAL CATALOG STATE')
    final = test('GET', '/pricing/catalog', expected=200, desc='Final catalog', headers=H)
    for c in final:
        margin_str = f'{c["profit_margin_percent"]}%' if c["profit_margin_percent"] is not None else 'None'
        price_str = f'${c["selling_price"]:.2f}' if c["selling_price"] is not None else 'None'
        print(f'     {c["item_name"]:20} WAC=${c["current_wac"]:>6.2f}  '
              f'Margin={margin_str:>6}  Price={price_str:>8}  Status={c["status"]}')

    print(f'\n{"=" * 60}')
    print(f'  📊 RESULTS: {passed}/{passed + failed} passed, {failed} failed')
    if failed == 0:
        print('  🎉 ALL TESTS PASSED!')
    else:
        print('  ❌ SOME TESTS FAILED')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
