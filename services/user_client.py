import httpx
import config
from logger import get_logger

log = get_logger(__name__)

# In-memory user context: telegram_id -> {user_id, role, display_name}
user_cache: dict[int, dict] = {}


async def create_user(telegram_id: int, display_name: str) -> dict:
    """POST /user — register or fetch user."""
    log.info("create_user called", extra={"telegram_id": telegram_id})

    if config.MOCK_SERVICES:
        user = {
            "user_id": f"mock-{telegram_id}",
            "role": "student",
        }
        user_cache[telegram_id] = {**user, "display_name": display_name}
        return user

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{config.USER_SERVICE_URL}/user",
            json={"telegram_id": str(telegram_id), "display_name": display_name},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        user_cache[telegram_id] = {**data, "display_name": display_name}
        return data


async def update_display_name(user_id: str, display_name: str) -> bool:
    """PUT /user — update display name."""
    log.info("update_display_name called", extra={"user_id": user_id})

    if config.MOCK_SERVICES:
        return True

    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{config.USER_SERVICE_URL}/user",
            json={"user_id": user_id, "display_name": display_name},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("success", False)


async def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    """GET /user?telegramId= — fetch user by telegram_id."""
    log.info("get_user_by_telegram_id called", extra={"telegram_id": telegram_id})

    # if telegram_id in user_cache:
    #     log.info("User found in cache", extra={"telegram_id": telegram_id})
    #     return user_cache[telegram_id]

    if config.MOCK_SERVICES:
        return user_cache.get(telegram_id)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.USER_SERVICE_URL}/user/{telegram_id}",
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        user_cache[telegram_id] = {**data, "display_name": data.get("display_name", "")}
        return data


# def get_cached_user(telegram_id: int) -> dict | None:
#     return user_cache.get(telegram_id)
