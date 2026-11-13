from fastapi import APIRouter

from app.api.v1.endpoints import alerts, brands, dashboard, health, imports, regions, sales

# Phase D/T08-T09 adds anomaly detection and alert management endpoints.
api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(brands.router, tags=["Brands"])
api_router.include_router(regions.router, tags=["Regions"])
api_router.include_router(imports.router, prefix="/imports", tags=["Imports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(sales.router, prefix="/sales", tags=["Sales"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
