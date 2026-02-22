from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.audit import AuditMiddleware
from app.database import engine, Base
from app.routers import auth, items, stock_ledger, bom, production, accounting, sales, reports, product_pricing

# Import all models so Base.metadata.create_all picks them up
import app.models  # noqa: F401

# Create all tables (development convenience — use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Manufacturing ERP System",
    description=(
        "Production-grade Manufacturing ERP with full accounting integration. "
        "Features: Item Master, Warehouse Management, Stock Ledger (weighted average), "
        "BOM with versioning, Production Orders, WIP tracking, Absorption Costing, "
        "Double-Entry Accounting, Sales, and Financial Reports."
    ),
    version="2.0.0",
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware
app.add_middleware(AuditMiddleware)

# Register routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(stock_ledger.router)
app.include_router(bom.router)
app.include_router(production.router)
app.include_router(accounting.router)
app.include_router(sales.router)
app.include_router(reports.router)
app.include_router(product_pricing.router)


@app.get("/")
def root():
    return {
        "message": "Manufacturing ERP System API v2.0",
        "docs": "/docs",
        "modules": [
            "Authentication & RBAC",
            "Item Master (Raw Materials & Finished Goods)",
            "Warehouse Management",
            "Stock Ledger (Weighted Average)",
            "Bill of Materials (Versioned)",
            "Production Orders",
            "WIP Management",
            "Production Expenses (Absorption Costing)",
            "Double-Entry Accounting",
            "Sales",
            "Financial Reports (Trial Balance, P&L, Balance Sheet)",
            "Sales Catalog & Product Pricing",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
