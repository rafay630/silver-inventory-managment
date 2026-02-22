# Manufacturing ERP System — Complete Technical Documentation

> **Version:** 2.0.0 · **Stack:** FastAPI + PostgreSQL + React · **Architecture:** Modular Monolith with Multi-Tenancy

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture & Design Principles](#2-architecture--design-principles)
3. [Infrastructure Layer](#3-infrastructure-layer)
4. [Database Schema — Deep Dive](#4-database-schema--deep-dive)
5. [Backend Modules — Deep Dive](#5-backend-modules--deep-dive)
   - [5.1 Authentication & RBAC](#51-authentication--rbac)
   - [5.2 Item Master & Inventory](#52-item-master--inventory)
   - [5.3 Stock Ledger (Weighted Average)](#53-stock-ledger-weighted-average)
   - [5.4 Bill of Materials (BOM)](#54-bill-of-materials-bom)
   - [5.5 Production Orders](#55-production-orders)
   - [5.6 WIP Management](#56-wip-management)
   - [5.7 Production Expenses (Absorption Costing)](#57-production-expenses-absorption-costing)
   - [5.8 Production Completion](#58-production-completion)
   - [5.9 Double-Entry Accounting](#59-double-entry-accounting)
   - [5.10 Sales](#510-sales)
   - [5.11 Sales Catalog & Product Pricing](#511-sales-catalog--product-pricing)
   - [5.12 Reports](#512-reports)
   - [5.13 Audit Middleware](#513-audit-middleware)
6. [Frontend — Deep Dive](#6-frontend--deep-dive)
   - [6.1 Application Shell & Routing](#61-application-shell--routing)
   - [6.2 Authentication Context](#62-authentication-context)
   - [6.3 API Service Layer](#63-api-service-layer)
   - [6.4 Dashboard](#64-dashboard)
   - [6.5 Inventory Pages](#65-inventory-pages)
   - [6.6 Manufacturing Pages](#66-manufacturing-pages)
   - [6.7 Sales Pages](#67-sales-pages)
   - [6.8 Accounting Page](#68-accounting-page)
   - [6.9 Reports Page](#69-reports-page)
7. [API Reference](#7-api-reference)
8. [Deployment & Configuration](#8-deployment--configuration)

---

## 1. System Overview

The **Manufacturing ERP System** is a full-stack, production-grade enterprise resource planning application designed for manufacturing companies. It covers the complete manufacturing lifecycle:

```
Raw Material Purchase → BOM → Production Order → WIP Issuance →
Expense Recording → Production Completion → Finished Goods →
Sales Catalog → Sales Order → Financial Reports
```

### Core Capabilities

| Module | Description |
|--------|------------|
| **Item Master** | Unified registry for raw materials and finished goods with SKU, barcode, UOM, and category support |
| **Warehouse Management** | Multi-warehouse support with per-warehouse stock tracking |
| **Stock Ledger** | Immutable, append-only ledger. All inventory math uses Weighted Average Cost (WAC) |
| **Bill of Materials** | Versioned BOMs with wastage %, UOM conversions, and material requirement calculations |
| **Production Orders** | Full lifecycle: Planned → In Progress → Completed/Cancelled |
| **WIP Management** | Material issuance to production with auto journal entries |
| **Production Expenses** | 7 expense types with full absorption costing |
| **Production Completion** | Cost calculation, finished goods receipt, and WIP clearance |
| **Double-Entry Accounting** | Chart of Accounts, balanced journal entries, Trial Balance, P&L, Balance Sheet |
| **Sales** | Sales orders with COGS + Revenue journal entries |
| **Sales Catalog** | Pricing management with margin %, publish/unpublish, and catalog-driven sales |
| **8 Reports** | Stock Ledger, Inventory Valuation, Production Cost Sheet, WIP Summary, Material Consumption, Trial Balance, P&L, Balance Sheet |
| **Audit Trail** | Every API request is logged with method, path, status, duration, and client IP |

---

## 2. Architecture & Design Principles

### 2.1 Modular Monolith

The application follows a modular monolith pattern where each domain has its own:
- **Model** (SQLAlchemy ORM)
- **Schema** (Pydantic validation/serialization)
- **Service** (business logic)
- **Router** (API endpoints)

```
backend/app/
├── models/          # 15 model files, 21 database tables
├── schemas/         # 6 schema files with Create/Update/Out patterns
├── services/        # 11 service classes with all business logic
├── routers/         # 9 router files defining all API endpoints
├── middleware/       # Audit logging middleware
├── config.py        # Environment-based configuration
├── database.py      # SQLAlchemy engine + session management
├── dependencies.py  # Auth + RBAC + tenant-scoping dependencies
└── main.py          # FastAPI app assembly
```

### 2.2 Multi-Tenancy

Every table (except `companies` itself) includes a `company_id` foreign key. Every query is scoped by the authenticated user's `company_id`, extracted via the `get_company_id` dependency. Data isolation is strict — no cross-tenant access is possible.

### 2.3 Immutable Stock Ledger

Stock is **never stored on items**. The `stock_ledger` table is append-only:
- `Current Stock = SUM(qty_in) - SUM(qty_out)` per `(item_id, warehouse_id)`
- `WAC = SUM(qty_in × unit_cost) / SUM(qty_in)` for inbound entries only

### 2.4 Automatic Double-Entry Accounting

Every inventory movement automatically creates balanced journal entries:
- **WIP Issue:** Dr Work In Progress, Cr Raw Material Inventory
- **Production Expense:** Dr Work In Progress, Cr Expense Account
- **Production Completion:** Dr Finished Goods Inventory, Cr Work In Progress
- **Sale:** Dr COGS + Dr Accounts Receivable, Cr Finished Goods + Cr Sales Revenue

---

## 3. Infrastructure Layer

### 3.1 Configuration (`config.py`)

Uses `pydantic-settings` with `.env` file support and `@lru_cache` for singleton access.

| Setting | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/silver_inventory` | Database connection string |
| `SECRET_KEY` | `your-super-secret-key...` | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token TTL (8 hours) |
| `PREVENT_NEGATIVE_STOCK` | `True` | Block operations that would create negative stock |

### 3.2 Database (`database.py`)

- **ORM:** SQLAlchemy with `declarative_base()`
- **Session:** Thread-safe `SessionLocal` with `autocommit=False`, `autoflush=False`
- **Connection Pooling:** `pool_pre_ping=True` for stale connection recovery
- **Dual DB Support:** Runtime detection of SQLite vs PostgreSQL connection args
- **Dependency Injection:** `get_db()` generator for request-scoped sessions

### 3.3 Dependencies (`dependencies.py`)

Three core dependencies used across all routers:

| Dependency | Purpose |
|-----------|---------|
| `get_current_user` | Decodes JWT → Fetches `User` record → Validates `is_active` |
| `require_roles(["admin", ...])` | Factory function returning a role-checker dependency |
| `get_company_id` | Extracts `company_id` from authenticated user for tenant scoping |

### 3.4 Docker (`docker-compose.yml`)

Provides PostgreSQL 16 Alpine with:
- Auto-created `silver_inventory` database
- Persistent volume `pgdata`
- Health check with `pg_isready`
- Exposed on port `5432`

---

## 4. Database Schema — Deep Dive

### 4.1 Entity-Relationship Overview

```mermaid
erDiagram
    companies ||--o{ users : "has"
    companies ||--o{ items : "owns"
    companies ||--o{ warehouses : "has"
    companies ||--o{ categories : "has"
    companies ||--o{ uom : "has"
    items ||--o{ stock_ledger : "tracked_in"
    warehouses ||--o{ stock_ledger : "stored_at"
    items ||--o{ bom_items : "ingredient_in"
    boms ||--o{ bom_items : "contains"
    items ||--o{ boms : "recipe_for"
    boms ||--o{ production_orders : "uses"
    production_orders ||--o{ wip_issues : "consumes"
    production_orders ||--o{ production_expenses : "incurs"
    production_orders ||--o{ production_requirements : "requires"
    wip_issues ||--o{ wip_issue_items : "contains"
    companies ||--o{ chart_of_accounts : "has"
    journal_entries ||--o{ journal_entry_lines : "contains"
    companies ||--o{ sales_orders : "has"
    sales_orders ||--o{ sales_order_items : "contains"
    items ||--o{ product_pricing : "priced_at"
```

### 4.2 All 21 Tables

#### Core Master Data

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`companies`** | `id`, `name`, `code`, `address`, `phone`, `email`, `is_active`, timestamps | PK: `id`, Unique: `code` | Tenant registry |
| **`users`** | `id`, `company_id`, `username`, `email`, `password_hash`, `full_name`, `role`, `is_active`, timestamps | PK: `id`, FK: `company_id` → companies | Users with roles: `admin`, `accountant`, `production_manager`, `store_manager` |
| **`categories`** | `id`, `company_id`, `name`, `description`, timestamps | PK: `id`, Unique: `(company_id, name)` | Item categorization |
| **`uom`** | `id`, `company_id`, `name`, `abbreviation`, timestamps | PK: `id`, Unique: `(company_id, name)` | Units of measure (kg, g, pcs, etc.) |
| **`uom_conversions`** | `id`, `company_id`, `from_uom_id`, `to_uom_id`, `conversion_factor`, timestamps | PK: `id`, Unique: `(company_id, from_uom_id, to_uom_id)` | Cross-UOM conversion factors |

#### Inventory

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`items`** | `id`, `company_id`, `name`, `sku`, `barcode`, `description`, `item_type`, `category_id`, `uom_id`, `base_cost`, `reorder_level`, `is_active`, timestamps | PK: `id`, Unique: `(company_id, sku)`, `(company_id, barcode)`, Index: `(company_id, item_type)` | Unified item master — `item_type` is either `raw_material` or `finished_good` |
| **`warehouses`** | `id`, `company_id`, `name`, `code`, `address`, `is_active`, timestamps | PK: `id`, Unique: `(company_id, code)` | Physical storage locations |
| **`stock_ledger`** | `id`, `company_id`, `item_id`, `warehouse_id`, `qty_in`, `qty_out`, `unit_cost`, `reference_type`, `reference_id`, `description`, `created_at` | PK: `id`, Index: `(company_id, item_id, warehouse_id)`, `(reference_type, reference_id)` | **Immutable, append-only.** `reference_type` values: `purchase`, `wip_issue`, `production_completion`, `sale`, `adjustment` |

#### Manufacturing

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`boms`** | `id`, `company_id`, `product_id`, `version`, `is_active`, `notes`, `created_by`, timestamps | PK: `id`, Unique: `(company_id, product_id, version)` | Bill of Materials header. Only one active BOM per product |
| **`bom_items`** | `id`, `bom_id`, `raw_item_id`, `quantity`, `wastage_percent`, `uom_id`, `conversion_factor` | PK: `id`, FK: `bom_id` (CASCADE), FK: `raw_item_id` | BOM line items with wastage & UOM conversion |
| **`production_orders`** | `id`, `company_id`, `order_number`, `product_id`, `bom_id`, `order_qty`, `completed_qty`, `warehouse_id`, `status`, `start_date`, `end_date`, `notes`, `created_by`, timestamps | PK: `id`, Unique: `(company_id, order_number)` | Status: `planned` → `in_progress` → `completed` / `cancelled` |
| **`production_requirements`** | `id`, `production_order_id`, `item_id`, `required_qty`, `available_qty`, `status` | PK: `id`, FK: `production_order_id` (CASCADE) | Snapshot of material requirements at order creation. Status: `adequate` / `insufficient` |
| **`wip_issues`** | `id`, `company_id`, `production_order_id`, `issue_number`, `issue_date`, `journal_entry_id`, `created_by`, `created_at` | PK: `id`, Unique: `(company_id, issue_number)` | Header for material issuance to production |
| **`wip_issue_items`** | `id`, `wip_issue_id`, `item_id`, `warehouse_id`, `quantity`, `unit_cost`, `total_cost` | PK: `id`, FK: `wip_issue_id` (CASCADE) | Individual raw materials issued with WAC at time of issue |
| **`production_expenses`** | `id`, `company_id`, `production_order_id`, `expense_type`, `description`, `amount`, `expense_date`, `journal_entry_id`, `created_by`, `created_at` | PK: `id`, Index: `(company_id, production_order_id)` | Expense types: `direct_labor`, `job_work`, `factory_rent`, `electricity`, `machine_depreciation`, `indirect_labor`, `lubricants` |

#### Accounting

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`chart_of_accounts`** | `id`, `company_id`, `code`, `name`, `account_type`, `parent_id`, `is_system`, `is_active`, timestamps | PK: `id`, Unique: `(company_id, code)` | `account_type`: `asset`, `liability`, `equity`, `income`, `expense`. System accounts are auto-seeded and protected |
| **`journal_entries`** | `id`, `company_id`, `entry_number`, `entry_date`, `reference_type`, `reference_id`, `description`, `is_system_generated`, `is_posted`, `created_by`, `created_at` | PK: `id`, Unique: `(company_id, entry_number)`, Index: `(reference_type, reference_id)` | `reference_type`: `wip_issue`, `production_expense`, `production_completion`, `sale` |
| **`journal_entry_lines`** | `id`, `journal_entry_id`, `account_id`, `debit`, `credit`, `description` | PK: `id`, FK: `journal_entry_id` (CASCADE) | Individual debit/credit lines. Every entry must balance: `SUM(debit) = SUM(credit)` |

#### Sales

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`sales_orders`** | `id`, `company_id`, `order_number`, `customer_name`, `order_date`, `status`, `total_amount`, `total_cost`, `notes`, `journal_entry_id`, `created_by`, timestamps | PK: `id`, Unique: `(company_id, order_number)` | Status: `draft`, `completed`, `cancelled` |
| **`sales_order_items`** | `id`, `sales_order_id`, `item_id`, `warehouse_id`, `quantity`, `unit_price`, `unit_cost`, `total_price` | PK: `id`, FK: `sales_order_id` (CASCADE) | Line items with both selling price and cost (for gross profit calculation) |
| **`product_pricing`** | `id`, `company_id`, `item_id`, `profit_margin_percent`, `selling_price`, `cost_basis`, `status`, `notes`, `created_by`, `updated_by`, timestamps | PK: `id`, Unique: `(company_id, item_id)` | Status: `draft` (not for sale) or `listed` (visible in Sales Order creation) |

#### Audit

| Table | Columns | Keys & Indexes | Purpose |
|-------|---------|----------------|---------|
| **`audit_logs`** | `id`, `company_id`, `user_id`, `action`, `entity_type`, `entity_id`, `old_values`, `new_values`, `ip_address`, `user_agent`, `created_at` | PK: `id`, Index: `(company_id, entity_type, entity_id)`, `(created_at)` | Tracks all data mutations. `old_values` and `new_values` stored as JSON strings |

### 4.3 Chart of Accounts — System Accounts

Auto-seeded for every new company:

| Code | Name | Type |
|------|------|------|
| `1100` | Raw Material Inventory | Asset |
| `1200` | Work In Progress | Asset |
| `1300` | Finished Goods Inventory | Asset |
| `1500` | Accounts Receivable | Asset |
| `2100` | Accounts Payable | Liability |
| `3100` | Owner's Equity | Equity |
| `4100` | Sales Revenue | Income |
| `5100` | Cost of Goods Sold | Expense |
| `5200` | Direct Labor | Expense |
| `5300` | Indirect Labor | Expense |
| `5400` | Electricity | Expense |
| `5500` | Factory Rent | Expense |
| `5600` | Machine Depreciation Expense | Expense |
| `5700` | Lubricants | Expense |
| `5800` | Job Work Expense | Expense |

---

## 5. Backend Modules — Deep Dive

### 5.1 Authentication & RBAC

**Files:** `routers/auth.py` · `services/auth_service.py` · `schemas/user.py` · `models/user.py` · `models/company.py` · `dependencies.py`

#### Auth Service (`auth_service.py`)

- **Password Hashing:** bcrypt via `passlib.context.CryptContext`
- **JWT Creation:** `jose.jwt.encode()` with payload `{sub: user_id, company_id, role, exp}`
- **Token Decoding:** Returns `TokenData(user_id, company_id, role)` or `None` on failure

#### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register-company` | None | Register a company + seed Chart of Accounts |
| `POST` | `/api/auth/register?company_id=<id>` | None | Register a user in an existing company |
| `POST` | `/api/auth/login` | None | Authenticate → returns JWT + `UserOut` |
| `GET`  | `/api/auth/me` | Bearer | Current user profile |

#### Roles

| Role | Permissions |
|------|------------|
| `admin` | Full access to all modules |
| `accountant` | Accounting operations, journal entries, financial reports |
| `production_manager` | Production orders, BOM, WIP, expenses, completions |
| `store_manager` | WIP issuance, inventory management |

---

### 5.2 Item Master & Inventory

**Files:** `routers/items.py` · `schemas/inventory.py` · `models/item.py` · `models/category.py` · `models/uom.py` · `models/warehouse.py`

This module manages all master data: **Categories**, **Units of Measure**, **Items**, and **Warehouses**.

#### Item Types

| Type | Examples | Usage |
|------|----------|-------|
| `raw_material` | Silver Wire, Silver Sheet, Solder Paste | Purchased, consumed in production |
| `finished_good` | Silver Ring, Silver Necklace | Produced via BOM, sold to customers |

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/categories` | Create a category |
| `GET`  | `/api/categories` | List categories |
| `POST` | `/api/uom` | Create a unit of measure |
| `GET`  | `/api/uom` | List UOMs |
| `POST` | `/api/uom/conversions` | Create a UOM conversion factor |
| `GET`  | `/api/uom/conversions` | List conversions |
| `POST` | `/api/items` | Create an item (raw material or finished good) |
| `GET`  | `/api/items` | List items (filterable by `item_type`, `is_active`) |
| `GET`  | `/api/items/{item_id}` | Get item detail |
| `PUT`  | `/api/items/{item_id}` | Update item fields |
| `GET`  | `/api/items/barcode/{barcode}` | Barcode lookup |
| `POST` | `/api/warehouses` | Create a warehouse |
| `GET`  | `/api/warehouses` | List warehouses |
| `PUT`  | `/api/warehouses/{warehouse_id}` | Update warehouse |
| `GET`  | `/api/warehouses/{warehouse_id}/stock` | Stock balances for a warehouse |

---

### 5.3 Stock Ledger (Weighted Average)

**Files:** `services/stock_ledger_service.py` · `routers/stock_ledger.py` · `models/stock_ledger.py`

The stock ledger is the **backbone of all inventory management**. It is immutable and append-only — no updates or deletes.

#### `StockLedgerService` Methods

| Method | Signature | Logic |
|--------|-----------|-------|
| `record_entry` | `(db, company_id, item_id, warehouse_id, qty_in, qty_out, unit_cost, reference_type, reference_id)` | Inserts an immutable row. If `qty_out > 0` and `PREVENT_NEGATIVE_STOCK` is enabled, validates sufficient balance before recording |
| `get_stock_balance` | `(db, company_id, item_id, warehouse_id?)` | Returns `SUM(qty_in) - SUM(qty_out)` |
| `get_weighted_average_cost` | `(db, company_id, item_id, warehouse_id?)` | Returns `SUM(qty_in × unit_cost) / SUM(qty_in)` for inbound entries only. Falls back to `item.base_cost` if no inbound entries exist |
| `get_all_balances` | `(db, company_id, item_type?, warehouse_id?)` | Returns all items with `{item_id, item_name, warehouse_id, warehouse_name, balance, weighted_avg_cost, total_value}` |
| `get_ledger_entries` | `(db, company_id, item_id?, warehouse_id?, reference_type?, limit, offset)` | Paginated ledger entries with filters |

#### Reference Types

| Type | Created By | Direction |
|------|-----------|-----------|
| `purchase` | Manual stock receipt | `qty_in` |
| `wip_issue` | `WIPService.issue_materials()` | `qty_out` |
| `production_completion` | `CompletionService.complete_production()` | `qty_in` |
| `sale` | `SalesService.create_sale()` | `qty_out` |
| `adjustment` | Manual adjustment | Either |

---

### 5.4 Bill of Materials (BOM)

**Files:** `services/bom_service.py` · `routers/bom.py` · `models/bom.py` · `schemas/production.py`

#### `BOMService` Methods

| Method | Description |
|--------|-------------|
| `create_bom` | Creates a versioned BOM. Validates product is `finished_good`, checks version uniqueness, deactivates previous active BOM if marking this one as active. Adds `BOMItem` entries for each raw material |
| `calculate_requirements` | Formula: `required_qty = order_qty × bom_qty × (1 + wastage_percent / 100) × conversion_factor` |
| `get_active_bom` | Returns the currently active BOM for a specific product |

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/bom/` | Create a BOM with items |
| `GET`  | `/api/bom/` | List BOMs (filter by `product_id`) |
| `GET`  | `/api/bom/{bom_id}` | Get BOM with items |
| `GET`  | `/api/bom/{bom_id}/requirements?order_qty=N` | Calculate material requirements for N units |

---

### 5.5 Production Orders

**Files:** `services/production_service.py` · `routers/production.py` · `models/production.py` · `schemas/production.py`

#### Lifecycle State Machine

```
planned ──→ in_progress ──→ completed
   │             │
   └─────────────┴──→ cancelled
```

- **`planned → in_progress`:** Via explicit `/start` endpoint or auto-triggered by first WIP issue
- **`in_progress → completed`:** When `completed_qty >= order_qty`
- **`cancelled`:** Only if no WIP issues exist

#### `ProductionService` Methods

| Method | Description |
|--------|-------------|
| `create_production_order` | Validates BOM matches product, calculates material requirements via `BOMService.calculate_requirements()`, snapshots requirements into `production_requirements` table with `adequate`/`insufficient` status based on current stock |
| `start_production` | Transitions status to `in_progress` (only from `planned`) |
| `cancel_production` | Transitions to `cancelled` (blocked if any WIP issues exist) |

#### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/production-orders/` | admin, production_manager | Create production order |
| `GET`  | `/api/production-orders/` | Any authenticated | List (filter by `status`) |
| `GET`  | `/api/production-orders/{id}` | Any authenticated | Detail with requirements |
| `POST` | `/api/production-orders/{id}/start` | admin, production_manager | Start production |
| `POST` | `/api/production-orders/{id}/cancel` | admin, production_manager | Cancel production |

---

### 5.6 WIP Management

**Files:** `services/wip_service.py` · `models/wip.py`

#### `WIPService.issue_materials()` — Step by Step

1. Validate production order exists and is in `planned` or `in_progress` status
2. Auto-transition to `in_progress` if currently `planned`
3. Generate issue number (`WIP-000001`)
4. For each raw material item:
   a. Get **Weighted Average Cost** from `StockLedgerService`
   b. Record `stock_ledger` entry (`qty_out`) — deducting from warehouse
   c. Calculate `total_cost = quantity × unit_cost`
5. Create journal entry:
   - **Dr** Work In Progress (1200) — total cost
   - **Cr** Raw Material Inventory (1100) — total cost
6. Link journal entry to WIP issue

#### API Endpoint

| Method | Endpoint | Auth |
|--------|----------|------|
| `POST` | `/api/production-orders/{id}/wip-issues` | admin, production_manager, store_manager |

---

### 5.7 Production Expenses (Absorption Costing)

**Files:** `services/expense_service.py` · `models/expense.py`

#### Expense Type → Account Mapping

| Expense Type | Account Code | Account Name |
|-------------|-------------|-------------|
| `direct_labor` | 5200 | Direct Labor |
| `indirect_labor` | 5300 | Indirect Labor |
| `electricity` | 5400 | Electricity |
| `factory_rent` | 5500 | Factory Rent |
| `machine_depreciation` | 5600 | Machine Depreciation Expense |
| `lubricants` | 5700 | Lubricants |
| `job_work` | 5800 | Job Work Expense |

#### `ExpenseService.record_expense()` — Step by Step

1. Validate expense type is in the allowed list
2. Validate production order exists and is `planned` or `in_progress`
3. Create `ProductionExpense` record
4. Create absorption costing journal entry:
   - **Dr** Work In Progress (1200) — amount
   - **Cr** Expense Account (mapped by type) — amount

#### API Endpoint

| Method | Endpoint | Auth |
|--------|----------|------|
| `POST` | `/api/production-orders/{id}/expenses` | admin, accountant, production_manager |

---

### 5.8 Production Completion

**Files:** `services/completion_service.py`

#### `CompletionService.complete_production()` — Step by Step

1. Validate production order is `in_progress`
2. Validate `completed_qty` doesn't exceed remaining quantity
3. Calculate costs:
   - `total_material_cost` = SUM of all WIP issue item costs
   - `total_expenses` = SUM of all production expenses
   - `total_production_cost` = material + expenses
   - `unit_cost` = total_production_cost / total_completed_qty
4. Insert `stock_ledger` entry: `qty_in = completed_qty`, `unit_cost = calculated`
5. Create journal entry:
   - **Dr** Finished Goods Inventory (1300)
   - **Cr** Work In Progress (1200)
6. Update order: increment `completed_qty`, set `status = "completed"` if fully complete

#### API Endpoint

| Method | Endpoint | Auth |
|--------|----------|------|
| `POST` | `/api/production-orders/{id}/complete` | admin, production_manager |

#### Return Payload

```json
{
  "production_order_id": "...",
  "order_number": "PO-000001",
  "completed_qty": 100,
  "total_completed": 100,
  "total_material_cost": 5000.00,
  "total_expenses": 2000.00,
  "total_production_cost": 7000.00,
  "unit_cost": 70.00,
  "journal_entry_id": "...",
  "status": "completed"
}
```

---

### 5.9 Double-Entry Accounting

**Files:** `services/accounting_service.py` · `routers/accounting.py` · `models/accounting.py` · `schemas/accounting.py`

#### `AccountingService` Methods

| Method | Description |
|--------|-------------|
| `seed_chart_of_accounts` | Auto-creates 15 system accounts for a new company |
| `get_account_by_code` | Lookup by code + company_id (raises 500 if not found, indicating data corruption) |
| `_next_entry_number` | Generates sequential `JE-000001` numbers per company |
| `create_journal_entry` | Creates a balanced journal entry. **Raises error if `total_debit ≠ total_credit`** |
| `get_trial_balance` | Aggregates all debit/credit per account, calculates net balances |
| `get_profit_and_loss` | Income − Expenses for a date range |
| `get_balance_sheet` | Assets = Liabilities + Equity as of a date. Includes retained earnings (net income) |

#### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/accounting/accounts` | admin, accountant | Create custom account |
| `GET`  | `/api/accounting/accounts` | Any | List accounts (filter by `account_type`) |
| `POST` | `/api/accounting/journal-entries` | admin, accountant | Create manual journal entry |
| `GET`  | `/api/accounting/journal-entries` | Any | List entries (filter by `reference_type`, date range) |
| `GET`  | `/api/accounting/journal-entries/{id}` | Any | Detail with lines |
| `GET`  | `/api/accounting/trial-balance` | Any | Trial Balance report |
| `GET`  | `/api/accounting/profit-and-loss` | Any | P&L report |
| `GET`  | `/api/accounting/balance-sheet` | Any | Balance Sheet report |

---

### 5.10 Sales

**Files:** `services/sales_service.py` · `routers/sales.py` · `models/sales.py` · `schemas/sales.py`

#### `SalesService.create_sale()` — Step by Step

1. Create `SalesOrder` header with auto-generated `order_number` (`SO-000001`)
2. For each line item:
   a. Validate item exists
   b. Get WAC from `StockLedgerService`
   c. Record `stock_ledger` entry (`qty_out`)
   d. Calculate line revenue and line COGS
3. Create compound journal entry (4 lines):
   - **Dr** Cost of Goods Sold (5100) — total COGS
   - **Cr** Finished Goods Inventory (1300) — total COGS
   - **Dr** Accounts Receivable (1500) — total revenue
   - **Cr** Sales Revenue (4100) — total revenue
4. Link journal entry to sales order

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sales/` | Create a sale |
| `GET`  | `/api/sales/` | List sales (filter by `status`) |
| `GET`  | `/api/sales/{id}` | Sale detail with items |

---

### 5.11 Sales Catalog & Product Pricing

**Files:** `services/product_pricing_service.py` · `routers/product_pricing.py` · `models/product_pricing.py` · `schemas/product_pricing.py`

#### `ProductPricingService` Methods

| Method | Description |
|--------|-------------|
| `list_catalog` | Returns all active finished goods with live WAC, stock, pricing status. Items without a pricing record appear as `"draft"` |
| `upsert_pricing` | Create or update pricing. Snapshots current WAC as `cost_basis`, calculates `selling_price = WAC × (1 + margin/100)`. Margin must be 0–500% |
| `publish_product` | Sets `status = "listed"`. Re-snapshots WAC and recomputes selling price at publish time |
| `unpublish_product` | Sets `status = "draft"`. Does not affect existing sales orders |
| `get_listed_items` | Returns only `listed` products with live stock and WAC — used by the sales order create modal |

#### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET`  | `/api/pricing/catalog` | Any | Full catalog |
| `POST` | `/api/pricing/` | admin | Set/update margin |
| `POST` | `/api/pricing/{id}/publish` | admin | Publish product |
| `POST` | `/api/pricing/{id}/unpublish` | admin | Unpublish product |
| `GET`  | `/api/pricing/listed` | Any | Listed items only |

---

### 5.12 Reports

**Files:** `services/report_service.py` · `routers/reports.py`

#### All 8 Reports

| # | Report | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | **Stock Ledger** | `GET /api/reports/stock-ledger` | Full ledger with running balance per entry. Filterable by item, warehouse, date range |
| 2 | **Inventory Valuation** | `GET /api/reports/inventory-valuation` | All items with WAC-based valuation. Delegates to `StockLedgerService.get_all_balances()` |
| 3 | **Production Cost Sheet** | `GET /api/reports/production-cost-sheet/{order_id}` | Detailed breakdown: material costs (per WIP issue item), expenses (per type), total production cost, unit cost |
| 4 | **WIP Summary** | `GET /api/reports/wip-summary` | All in-progress orders with material cost, expense cost, and total WIP value |
| 5 | **Material Consumption** | `GET /api/reports/material-consumption` | Raw material consumption grouped by item, with total quantity and total cost |
| 6 | **Trial Balance** | `GET /api/reports/trial-balance` | Delegates to `AccountingService.get_trial_balance()` |
| 7 | **Profit & Loss** | `GET /api/reports/profit-and-loss` | Delegates to `AccountingService.get_profit_and_loss()` |
| 8 | **Balance Sheet** | `GET /api/reports/balance-sheet` | Delegates to `AccountingService.get_balance_sheet()` |

---

### 5.13 Audit Middleware

**File:** `middleware/audit.py`

ASGI middleware using Starlette's `BaseHTTPMiddleware`. Logs every request:

```
POST /api/production-orders/ status=201 duration=0.045s client=127.0.0.1
```

Fields logged: `method`, `path`, `status_code`, `duration`, `client_ip`.

---

## 6. Frontend — Deep Dive

### 6.1 Application Shell & Routing

**Files:** `App.jsx` · `components/layout/AppLayout.jsx` · `components/layout/Sidebar.jsx`

#### Architecture

```
<BrowserRouter>
  <AuthProvider>
    <AppRoutes>
      ├── /login          → <Login />
      ├── / (protected)   → <AppLayout> (Sidebar + Outlet)
      │   ├── /            → <Dashboard />
      │   ├── /items       → <ItemList />
      │   ├── /warehouses  → <WarehouseList />
      │   ├── /stock-ledger → <StockLedger />
      │   ├── /bom         → <BOMList />
      │   ├── /production  → <ProductionOrders />
      │   ├── /sales       → <SalesOrders /> (includes Sales Catalog tab)
      │   ├── /accounting  → <Accounting />
      │   └── /reports     → <Reports />
      └── * → redirect to /
    </AppRoutes>
  </AuthProvider>
</BrowserRouter>
```

#### `ProtectedRoute` component

Checks `useAuth()` state:
- If `loading`: render loading spinner
- If `!user`: redirect to `/login`
- Otherwise: render children

#### `AppLayout`

Renders a collapsible sidebar (`<Sidebar />`) alongside the main content area (`<Outlet />`).

---

### 6.2 Authentication Context

**File:** `context/AuthContext.jsx`

React Context providing global auth state:

| Export | Type | Purpose |
|--------|------|---------|
| `AuthProvider` | Component | Wraps app, manages `user` state |
| `useAuth()` | Hook | Returns `{ user, login, logout, loading }` |

**Persistence:** Token and user data stored in `localStorage`. On mount, restores from storage if available.

**Login flow:** `authAPI.login()` → saves token + user → sets state.

**Logout flow:** Clears `localStorage` → sets user to `null`.

---

### 6.3 API Service Layer

**File:** `services/api.js`

Centralized Axios instance with:
- **Base URL:** `/api` (proxied by Vite dev server to `localhost:8000`)
- **Request Interceptor:** Attaches `Bearer <token>` from localStorage
- **Response Interceptor:** On `401`, clears storage and redirects to `/login` (unless already on login)

#### 10 API Modules

| Module | Methods |
|--------|---------|
| `authAPI` | `login`, `me` |
| `itemsAPI` | `list`, `get`, `create`, `update`, `getByBarcode` |
| `categoriesAPI` | `list`, `create` |
| `uomAPI` | `list`, `create`, `listConversions`, `createConversion` |
| `warehousesAPI` | `list`, `create`, `update`, `getStock` |
| `stockLedgerAPI` | `entries`, `balance`, `balances` |
| `bomAPI` | `list`, `get`, `create`, `requirements` |
| `productionAPI` | `list`, `get`, `create`, `start`, `cancel`, `issueWIP`, `recordExpense`, `complete` |
| `salesAPI` | `list`, `get`, `create` |
| `accountingAPI` | `listAccounts`, `createAccount`, `listJournalEntries`, `getJournalEntry`, `createJournalEntry`, `trialBalance`, `profitAndLoss`, `balanceSheet` |
| `pricingAPI` | `getCatalog`, `setPricing`, `publish`, `unpublish`, `getListed` |
| `reportsAPI` | `stockLedger`, `inventoryValuation`, `productionCostSheet`, `wipSummary`, `materialConsumption`, `trialBalance`, `profitAndLoss`, `balanceSheet` |

---

### 6.4 Dashboard

**File:** `pages/Dashboard.jsx`

A data-rich dashboard that aggregates live metrics from multiple APIs on mount:

| Stat Card | Source |
|-----------|--------|
| Total Items | `itemsAPI.list()` |
| Items in Stock | `stockLedgerAPI.balances()` |
| Active Production Orders | `productionAPI.list()` |
| Total Sales | `salesAPI.list()` |
| Revenue | Sum of `total_amount` from sales |
| Gross Profit | Revenue − Sum of `total_cost` |

**Visualizations:**
- Bar chart showing top items by total inventory value (Recharts library)
- Quick-action buttons to navigate to key modules

**Libraries:** `react-icons/hi` for icons, `recharts` for charts.

---

### 6.5 Inventory Pages

#### 6.5.1 Item List (`pages/inventory/ItemList.jsx`)

- **View:** Tabular list of all items (raw materials + finished goods)
- **Features:** Create item modal, edit item, filter by type, search, toggle active/inactive
- **API:** `itemsAPI`, `categoriesAPI`, `uomAPI`

#### 6.5.2 Warehouse List (`pages/inventory/WarehouseList.jsx`)

- **View:** List of warehouses with stock summary
- **Features:** Create/edit warehouse, view warehouse stock
- **API:** `warehousesAPI`

#### 6.5.3 Stock Ledger (`pages/inventory/StockLedger.jsx`)

- **View:** Chronological ledger of all stock movements
- **Features:** Filter by item, warehouse, reference type. Shows running balance
- **API:** `stockLedgerAPI`

---

### 6.6 Manufacturing Pages

#### 6.6.1 BOM List (`pages/manufacturing/BOMList.jsx`)

- **View:** List of all Bills of Materials
- **Features:** Create BOM with multiple raw material items, set wastage %, version management, activate/deactivate
- **API:** `bomAPI`, `itemsAPI`

#### 6.6.2 Production Orders (`pages/manufacturing/ProductionOrders.jsx`)

- **View:** Production order list with status badges
- **Features:**
  - Create production order (select product → auto-load active BOM → set quantity)
  - Start production, cancel production
  - Issue WIP materials (select items, quantities, warehouse)
  - Record expenses (7 types with amounts)
  - Complete production (set completed quantity)
- **API:** `productionAPI`, `itemsAPI`, `bomAPI`, `warehousesAPI`, `stockLedgerAPI`

---

### 6.7 Sales Pages

#### 6.7.1 Sales Orders (`pages/sales/SalesOrders.jsx`)

**Tabbed layout** with two tabs:

**Tab 1: Sales Orders**
- Lists all sales orders with order number, customer, date, amount, status
- "New Sale" modal:
  - Item dropdown filtered to **listed products** from catalog (falls back to all finished goods if none listed)
  - **Auto-fills unit price** from catalog selling price when item is selected
  - Price hint text: "Auto-filled from catalog"
- **API:** `salesAPI`, `pricingAPI.getListed()`, `itemsAPI`, `warehousesAPI`

**Tab 2: Sales Catalog**
- Renders `<SalesCatalog />` component

#### 6.7.2 Sales Catalog (`pages/sales/SalesCatalog.jsx`)

- **Summary Stats:** Total Finished Goods, Listed, Draft
- **Data Table:** Product name, SKU, stock, WAC, profit margin (editable for admins), selling price, status badge
- **Admin Controls:**
  - **Save Margin:** Input margin % → saves via `pricingAPI.setPricing()`
  - **Publish:** Makes product available for sales
  - **Unpublish:** Removes from sales catalog
- **RBAC:** Non-admin users see the table but cannot edit margins or publish/unpublish
- **API:** `pricingAPI`

---

### 6.8 Accounting Page

**File:** `pages/accounting/Accounting.jsx`

- **Chart of Accounts:** Tree/list view of all accounts, create custom accounts
- **Journal Entries:** List with date/amount/description, view entry detail with debit/credit lines
- **Financial Reports:** Inline Trial Balance, P&L, Balance Sheet rendering
- **API:** `accountingAPI`

---

### 6.9 Reports Page

**File:** `pages/reports/Reports.jsx`

Tabbed interface providing access to all 8 reports:

1. **Stock Ledger Report** — Filterable ledger with running balance
2. **Inventory Valuation** — WAC-based valuation summary
3. **Production Cost Sheet** — Per-order cost breakdown
4. **WIP Summary** — All active production with cost tracking
5. **Material Consumption** — Grouped by raw material
6. **Trial Balance** — Debit/credit per account
7. **Profit & Loss** — Income vs expenses
8. **Balance Sheet** — Assets = Liabilities + Equity

**API:** `reportsAPI`

---

## 7. API Reference

### Complete Endpoint Map

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| **Auth** | `/api/auth` | 4 endpoints |
| **Items** | `/api` | 16 endpoints (categories, UOMs, items, warehouses) |
| **Stock Ledger** | `/api/stock-ledger` | 3 endpoints |
| **BOM** | `/api/bom` | 4 endpoints |
| **Production** | `/api/production-orders` | 8 endpoints (orders, WIP, expenses, completion) |
| **Accounting** | `/api/accounting` | 8 endpoints (accounts, journal entries, financial reports) |
| **Sales** | `/api/sales` | 3 endpoints |
| **Pricing** | `/api/pricing` | 5 endpoints |
| **Reports** | `/api/reports` | 8 endpoints |
| **Total** | | **~59 endpoints** |

### Authentication

All endpoints (except auth routes) require `Authorization: Bearer <JWT>` header. Roles are enforced per-endpoint.

### Error Handling

| Status | Meaning |
|--------|---------|
| `400` | Validation error, business rule violation (e.g., insufficient stock, invalid expense type) |
| `401` | Missing or invalid JWT |
| `403` | Insufficient role permissions |
| `404` | Entity not found |
| `500` | Internal server error |

---

## 8. Deployment & Configuration

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (or Docker)

### Quick Start

```bash
# 1. Start PostgreSQL
docker-compose up -d

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure DATABASE_URL and SECRET_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev  # Vite dev server on port 5173
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key (change in production!) |
| `ALGORITHM` | No | Default: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: `480` |
| `PREVENT_NEGATIVE_STOCK` | No | Default: `True` |

### API Documentation

FastAPI auto-generates interactive docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

> **Document generated on:** 2026-02-22 · **System version:** 2.0.0
