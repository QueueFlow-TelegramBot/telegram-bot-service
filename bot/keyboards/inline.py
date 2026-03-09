from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def rooms_keyboard(rooms: list[dict]) -> InlineKeyboardMarkup:
    """Build an inline keyboard from a list of rooms."""
    buttons = [
        [InlineKeyboardButton(
            text=f"{r['room_name']} ({'active' if r.get('active') else 'inactive'})",
            callback_data=f"room:{r['room_id']}",
        )]
        for r in rooms
    ]
    return InlineKeyboardMarkup(buttons)


def next_keyboard(rooms: list[dict]) -> InlineKeyboardMarkup:
    """Build an inline keyboard for calling next in a room."""
    buttons = [
        [InlineKeyboardButton(
            text=f"Next in {r['room_name']}",
            callback_data=f"next:{r['room_id']}",
        )]
        for r in rooms
        if r.get("active")
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Build a confirm/cancel keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Confirm", callback_data=f"confirm:{action}:{data}"),
            InlineKeyboardButton("Cancel", callback_data="cancel"),
        ]
    ])
