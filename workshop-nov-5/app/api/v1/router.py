from fastapi import APIRouter

from app.api.v1.endpoints import analytics, export_pro, export_vibe, links

api_router = APIRouter()
api_router.include_router(links.router)
api_router.include_router(analytics.router)
api_router.include_router(export_vibe.router)
api_router.include_router(export_pro.router)
