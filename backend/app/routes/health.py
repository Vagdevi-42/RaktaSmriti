from fastapi import APIRouter
from ..database import get_table

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    try:
        table = get_table()
        table.table_status
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "detail": str(e)}