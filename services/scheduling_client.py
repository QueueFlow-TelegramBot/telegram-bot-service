import httpx
import config
from logger import get_logger

from services.user_client import get_user_by_telegram_id

log = get_logger(__name__)


async def create_room(room_name: str, creator_id: str) -> dict:
    """POST /rooms — create a new queue room."""
    log.info("create_room called", extra={"room_name": room_name})

    user = await get_user_by_telegram_id(creator_id)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms",
            json={"name": room_name, "creator_id": str(creator_id), "creator_name": user.get("display_name", "Unknown")},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def get_rooms(creator_id: str) -> list[dict]:
    """GET /rooms?creatorId= — list rooms for a creator."""
    log.info("get_rooms called", extra={"creator_id": creator_id})

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.SCHEDULING_SERVICE_URL}/rooms",
            params={"creator_id": creator_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("rooms", [])


async def join_room(room_id: str, user_id: str) -> dict:
    """POST /rooms/{room_id}/join — join a queue."""
    log.info("join_room called", extra={"room_id": room_id, "user_id": user_id})

    user = await get_user_by_telegram_id(user_id)
    body = {"user_id": str(user_id), "user_name": user.get("display_name", "Unknown")}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms/{room_id}/join",
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def next_in_queue(room_id: str, creator_id: str) -> dict:
    """POST /rooms/{room_id}/next — call next person."""
    log.info("next_in_queue called", extra={"room_id": room_id, "creator_id": creator_id})

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms/{room_id}/next",
            json={"creator_id": str(creator_id)},
            timeout=10,
        )
        resp.raise_for_status()

        if resp.status_code == 204:
            return {"error": "queue_empty"}

        return resp.json()
