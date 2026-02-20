from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.audit import AuditMiddleware
from app.database import engine, Base
from app.routers import auth, users, suppliers, raw_materials, products, production, inventory, reports

# Create all tables (development convenience — use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Silver & Brass Manufacturing Inventory System",
    description="ERP system for manufacturing inventory management — raw materials, production, WIP, finished goods, wastage tracking, and reporting.",
    version="1.0.0",
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

# Custom middleware
app.add_middleware(AuditMiddleware)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(suppliers.router)
app.include_router(raw_materials.router)
app.include_router(products.router)
app.include_router(production.router)
app.include_router(inventory.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"message": "Silver & Brass Manufacturing Inventory System API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
