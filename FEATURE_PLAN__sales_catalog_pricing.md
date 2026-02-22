# Feature Plan: Sales Catalog & Product Pricing Panel

## Context

This is the **Silver Inventory Management** system — a full-stack Manufacturing ERP
(FastAPI + SQLAlchemy backend, React 18 + Vite frontend).

The system already calculates the **finished-good unit cost** at the end of every
production run (`ProductionOrder.unit_cost` = total absorbed cost ÷ completed qty).
It also stores the current **Weighted Average Cost (WAC)** for every finished good
in the stock ledger.

Currently, when creating a Sales Order, the operator must **manually type a unit
price** in the modal with no reference price. There is no governed, admin-controlled
pricing layer between production cost and customer sale price.

---

## Feature Goal

Build a **Sales Catalog Panel** — a new tab inside the existing `/sales` route —
where:

1. All active finished goods are listed with their current WAC (cost price) visible.
2. Items appear as **"Draft / Not Listed"** by default — they cannot be selected in
   a Sales Order until an admin publishes them.
3. An **admin-only action** allows setting a **profit margin %** on each product,
   which auto-calculates and stores a `selling_price`.
4. Once an admin clicks **"Publish"**, the product becomes **"Listed"** and its
   `selling_price` is locked in as the default unit price in new Sales Orders.
5. The admin can **edit the margin or unpublish** at any time (unpublishing does NOT
   affect existing sales orders — they are immutable).

---

## What NOT to change

- The `SalesOrder`, `SalesOrderItem`, `StockLedger`, and all journal-entry logic
  remain completely untouched.
- The `Item` model itself should NOT be modified — use a separate pricing table
  (see below) to keep master data clean and auditable.
- Existing Sales Order creation flow stays — but the item dropdown should now
  **only show "Listed" products**, and the unit price field should **pre-fill**
  with `selling_price` (still editable by the operator for discounts).

---

## Backend Changes

### 1. New Model — `ProductPricing`

**File:** `backend/app/models/product_pricing.py`

```python
class ProductPricing(Base):
    __tablename__ = "product_pricing"

    id           = Column(UUID, primary_key=True, default=uuid4)
    company_id   = Column(UUID, ForeignKey("companies.id"), nullable=False)
    item_id      = Column(UUID, ForeignKey("items.id"), nullable=False, unique=True)
                   # One pricing record per finished good per company
    profit_margin_percent = Column(Float, nullable=False, default=0.0)
    selling_price         = Column(Float, nullable=False, default=0.0)
                   # stored = WAC_at_publish_time * (1 + margin/100)
    cost_basis            = Column(Float, nullable=False, default=0.0)
                   # snapshot of WAC at the time admin set the margin
    status       = Column(String, default="draft")  # "draft" | "listed"
    notes        = Column(String, nullable=True)
    created_by   = Column(UUID, ForeignKey("users.id"))
    updated_by   = Column(UUID, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    item    = relationship("Item")
    company = relationship("Company")
```

Import this model in `main.py` so `create_all` picks it up.

---

### 2. New Schema — `product_pricing.py`

**File:** `backend/app/schemas/product_pricing.py`

```python
class ProductPricingCreate(BaseModel):
    item_id: UUID
    profit_margin_percent: float  # e.g. 25.0 for 25%
    notes: Optional[str] = None

class ProductPricingUpdate(BaseModel):
    profit_margin_percent: Optional[float]
    notes: Optional[str]

class ProductPricingOut(BaseModel):
    id: UUID
    item_id: UUID
    item_name: str          # joined from Item
    item_sku: str
    profit_margin_percent: float
    cost_basis: float       # WAC at time of last save
    selling_price: float    # computed: cost_basis * (1 + margin/100)
    status: str             # "draft" | "listed"
    notes: Optional[str]
    current_wac: float      # live WAC from stock ledger (may differ from cost_basis)
    current_stock: float    # live stock balance
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

### 3. New Service — `product_pricing_service.py`

**File:** `backend/app/services/product_pricing_service.py`

Implement these methods:

| Method | Logic |
|--------|-------|
| `list_catalog(db, company_id)` | Query all `Item` where `item_type="finished_good"` and `is_active=True`. Left-join `ProductPricing`. For each, fetch live WAC + stock balance from `StockLedgerService`. Return merged list. |
| `upsert_pricing(db, company_id, item_id, margin_percent, notes, user_id)` | Get live WAC for the item. Compute `selling_price = WAC * (1 + margin/100)`. Upsert `ProductPricing` row (insert if not exists, update if exists). Status stays `"draft"` unless already `"listed"`. |
| `publish_product(db, company_id, pricing_id, user_id)` | Set `status = "listed"`. Re-snapshot WAC and recompute `selling_price`. |
| `unpublish_product(db, company_id, pricing_id, user_id)` | Set `status = "draft"`. Does NOT modify any existing sales order. |
| `get_listed_items(db, company_id)` | Returns only `status="listed"` records. Used by Sales Order create modal. |

> **Important**: `upsert_pricing` must call `StockLedgerService.get_weighted_average_cost`
> for the `cost_basis` snapshot — same service already used by Production Completion.

---

### 4. New Router — `product_pricing.py`

**File:** `backend/app/routers/product_pricing.py`  
**Prefix:** `/api/pricing`

| Endpoint | Method | Auth Roles | Description |
|----------|--------|------------|-------------|
| `/catalog` | GET | any authenticated | Full catalog — all finished goods with pricing status, WAC, stock |
| `/` | POST | admin only | Create/update pricing for a product (sets margin) |
| `/{id}/publish` | POST | admin only | Publish product → status = "listed" |
| `/{id}/unpublish` | POST | admin only | Unpublish product → status = "draft" |
| `/listed` | GET | any authenticated | Only listed products (for Sales Order item dropdown) |

Register the router in `main.py`:
```python
from app.routers import product_pricing
app.include_router(product_pricing.router)
```

---

### 5. Modify Sales Order Item Dropdown (backend)

In `sales_service.py` / `sales.py` router, no logic changes needed —
the restriction to listed items is enforced on the **frontend** (see below).
The backend should still accept any valid finished-good `item_id` so existing
orders are not broken.

---

## Frontend Changes

### 1. Add API methods — `api.js`

Add a new `pricingAPI` export:

```js
export const pricingAPI = {
  getCatalog:   () => axios.get('/pricing/catalog'),
  setPricing:   (data) => axios.post('/pricing', data),
  publish:      (id) => axios.post(`/pricing/${id}/publish`),
  unpublish:    (id) => axios.post(`/pricing/${id}/unpublish`),
  getListed:    () => axios.get('/pricing/listed'),
}
```

---

### 2. New Tab in `SalesOrders.jsx`

The `/sales` route currently has a single view (orders table). Convert it to a
**two-tab layout** matching the pattern used in `StockLedger.jsx`:

| Tab | Content |
|-----|---------|
| **Sales Orders** | Existing orders table — unchanged |
| **Sales Catalog** | New pricing panel (see below) |

---

### 3. New Component — `SalesCatalog` (inside `SalesOrders.jsx` or separate file)

**Layout:**

- Page header: "Sales Catalog" + subtitle "Set profit margins and publish products for sale"
- **Stat bar** (3 cards): Total Finished Goods | Listed (ready to sell) | Draft (pending review)
- **Table** with columns:

| Column | Detail |
|--------|--------|
| Product | Item name + SKU badge |
| Current Stock | Live balance from stock ledger |
| Cost (WAC) | Live weighted average cost — shown in amber to indicate it may change |
| Margin % | Input field (editable inline for admins, read-only for others) |
| Selling Price | Auto-calculated: `WAC × (1 + margin/100)` — updates live as margin changes |
| Status | Badge: green "Listed" / gray "Draft" |
| Actions | "Save Margin" button + "Publish" / "Unpublish" toggle (admin only, hidden for other roles) |

**Behavior rules:**

- If the user's role is NOT `admin`, the Margin % column is **read-only** and action
  buttons are hidden. Other roles can VIEW the catalog but not modify it.
- Margin input is a number field (0–500%). Selling price updates in real-time as the
  admin types (purely cosmetic JS calculation — not saved until "Save Margin" is clicked).
- "Save Margin" sends `POST /api/pricing` — on success, refreshes the row.
- "Publish" sends `POST /api/pricing/{id}/publish` — status badge flips to green "Listed".
- "Unpublish" sends `POST /api/pricing/{id}/unpublish` — status badge flips to gray "Draft".
- Show a **warning tooltip** on the WAC column: "Cost may change as new production
  batches complete. Re-publish to lock in updated selling price."
- Items with **zero stock** should show a subtle "No Stock" indicator but still be
  publishable (pre-listing is valid).

---

### 4. Modify Sales Order Create Modal

In the existing **Create Sale** modal in `SalesOrders.jsx`:

- The **item dropdown** should call `pricingAPI.getListed()` instead of
  `itemsAPI.list({ item_type: 'finished_good' })`. This restricts selection
  to published products only.
- When an item is selected from the dropdown, **auto-populate the unit price field**
  with the item's `selling_price` from the catalog.
- The price field remains **editable** (to allow discounts or custom pricing per order).
- Add a small helper text below the price field: "Default: catalog price. Edit to apply discount."

---

## Routing & Sidebar

No new route needed — the Catalog is a tab inside `/sales`.

No sidebar change needed. The existing "Sales Orders" link navigates to `/sales`
which now shows both tabs.

---

## Role & Permission Summary

| Action | admin | accountant | production_manager | store_manager |
|--------|-------|------------|--------------------|---------------|
| View catalog | ✅ | ✅ | ✅ | ✅ |
| Set / edit margin | ✅ | ❌ | ❌ | ❌ |
| Publish / Unpublish | ✅ | ❌ | ❌ | ❌ |
| Create Sales Order (listed items) | ✅ | ✅ | ❌ | ✅ |

---

## Data Flow Summary

```
ProductionOrder.complete()
  → unit_cost calculated & stored
  → Finished Goods inventory updated (StockLedger)
  → WAC updated automatically

Admin opens Sales Catalog tab
  → sees all finished goods with live WAC
  → enters profit_margin_percent (e.g. 30%)
  → selling_price = WAC × 1.30  (shown live)
  → clicks "Save Margin"  → ProductPricing row upserted (status: draft)
  → clicks "Publish"      → status = "listed", cost_basis + selling_price locked

Operator creates a Sales Order
  → item dropdown shows only "listed" products
  → unit price pre-filled with catalog selling_price
  → operator can adjust for discount
  → sale proceeds as normal (journal entries unchanged)
```

---

## Files to Create / Modify

**New files:**
- `backend/app/models/product_pricing.py`
- `backend/app/schemas/product_pricing.py`
- `backend/app/services/product_pricing_service.py`
- `backend/app/routers/product_pricing.py`

**Modified files:**
- `backend/app/main.py` — import new model + register new router
- `frontend/src/services/api.js` — add `pricingAPI`
- `frontend/src/pages/sales/SalesOrders.jsx` — add Catalog tab + modify create modal

---

## Implementation Notes

1. **WAC source**: Always use `StockLedgerService.get_weighted_average_cost()` —
   the same method used in `wip_service.py` and `sales_service.py`. Do not hardcode
   or duplicate this logic.

2. **Upsert pattern**: Use SQLAlchemy's query-then-update pattern (not `merge`) to
   avoid session conflicts. Check if a `ProductPricing` row exists for
   `(company_id, item_id)` before deciding to INSERT or UPDATE.

3. **Multi-tenancy**: Every query in the new service must filter by `company_id`,
   consistent with every other service in this codebase.

4. **No accounting entries**: Setting a price or publishing a product creates NO
   journal entries. The accounting impact only occurs when a Sale is created
   (existing behavior, unchanged).

5. **Existing Sales Orders**: Because item filtering is frontend-only, existing orders
   that reference items which later get unpublished will still display correctly —
   `SalesOrderItem` stores `unit_price` as a literal value, not a foreign key to pricing.
