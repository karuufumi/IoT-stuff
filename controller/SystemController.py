from fastapi import APIRouter, HTTPException
from data.mongo import mongo

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
async def health_check():
    """
    Application + MongoDB health check.
    """
    try:
        # MongoDB ping
        await mongo.client.admin.command("ping") # type: ignore
        return {
            "status": "ok",
            "mongodb": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "mongodb": "disconnected",
                "reason": str(e),
            },
        )