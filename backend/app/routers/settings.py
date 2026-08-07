from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/")
def get_settings():
    return {
        "minDoorWidth": 0.9,
        "minRoomArea": 9.0,
        "corridorWidth": 1.0
    }
