import uuid
import httpx
import config
from logger import get_logger

from bot.notifications.publisher import rabbitmq_publisher
from services.user_client import get_user_by_telegram_id

log = get_logger(__name__)

# Mock in-memory store: room_id -> {room_id, room_name, creator_id, active}
_mock_rooms: dict[str, dict] = {}


async def create_room(room_name: str, creator_id: str) -> dict:
    """POST /rooms — create a new queue room."""
    log.info("create_room called", extra={"room_name": room_name})

    if config.MOCK_SERVICES:
        room_id = str(uuid.uuid4())[:8]
        _mock_rooms[room_id] = {
            "room_id": room_id,
            "room_name": room_name,
            "creator_id": creator_id,
            "active": True,
        }
        return {"room_id": room_id}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms",
            json={"room_name": room_name, "creator_id": creator_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def get_rooms(creator_id: str) -> list[dict]:
    """GET /rooms?creatorId= — list rooms for a creator."""
    log.info("get_rooms called", extra={"creator_id": creator_id})

    if config.MOCK_SERVICES:
        return [
            {"room_id": r["room_id"], "room_name": r["room_name"], "active": r["active"]}
            for r in _mock_rooms.values()
            if r["creator_id"] == creator_id
        ]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.SCHEDULING_SERVICE_URL}/rooms",
            params={"creatorId": creator_id},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("rooms", [])


async def join_room(room_id: str, user_id: str) -> dict:
    """POST /rooms/{room_id}/join — join a queue."""
    log.info("join_room called", extra={"room_id": room_id, "user_id": user_id})

    if config.MOCK_SERVICES:
        room = _mock_rooms.get(room_id)
        return {
            "no_of_people_in_front": 3,
            "room_name": room["room_name"] if room else room_id,
            "creator_name": "Secretary",
        }

    user = await get_user_by_telegram_id(user_id)
    body = {"user_id": str(user_id), "user_name": user.get("display_name", "Unknown")}
    rabbitmq_publisher.publish(
        routing_key=f"room.{room_id}",
        body=body,
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms/{room_id}/join",
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def next_in_queue(room_id: str) -> dict:
    """POST /rooms/{room_id}/next — call next person."""
    log.info("next_in_queue called", extra={"room_id": room_id})

    if config.MOCK_SERVICES:
        return {"success": True}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.SCHEDULING_SERVICE_URL}/rooms/{room_id}/next",
            json={},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
