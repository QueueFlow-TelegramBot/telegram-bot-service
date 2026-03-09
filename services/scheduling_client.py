import httpx
import config
from logger import get_logger

log = get_logger(__name__)


async def create_room(room_name: str, creator_id: str) -> dict:
    """POST /room — create a new queue room."""
    log.info("create_room called", extra={"room_name": room_name})

    if config.MOCK_SERVICES:
        return {"room_id": "room-001"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/room",
            json={"room_name": room_name, "creator_id": creator_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def get_rooms(creator_id: str) -> list[dict]:
    """GET /room?creatorId= — list rooms for a creator."""
    log.info("get_rooms called", extra={"creator_id": creator_id})

    if config.MOCK_SERVICES:
        return [
            {"room_id": "room-001", "room_name": "Reception A", "active": True},
            {"room_id": "room-002", "room_name": "Reception B", "active": True},
        ]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.SCHEDULING_SERVICE_URL}/room",
            params={"creatorId": creator_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("rooms", [])


async def join_room(room_id: str, user_id: str) -> dict:
    """POST /room/{room_id}/user — join a queue."""
    log.info("join_room called", extra={"room_id": room_id, "user_id": user_id})

    if config.MOCK_SERVICES:
        return {
            "no_of_people_in_front": 3,
            "room_name": "Reception A",
            "creator_name": "Secretary",
        }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/room/{room_id}/user",
            json={"user_id": user_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def next_in_queue(room_id: str) -> dict:
    """POST /room/{room_id}/next — call next person."""
    log.info("next_in_queue called", extra={"room_id": room_id})

    if config.MOCK_SERVICES:
        return {"success": True}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/room/{room_id}/next",
            json={},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
