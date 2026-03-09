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


def room_actions_keyboard(room_id: str) -> InlineKeyboardMarkup:
    """Build action buttons for a selected room."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Call next", callback_data=f"confirm_next:{room_id}")],
        [InlineKeyboardButton("Copy room ID", callback_data=f"copyid:{room_id}")],
    ])


def cancel_confirm_keyboard(room_id: str) -> InlineKeyboardMarkup:
    """Confirm leaving the queue."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, leave", callback_data=f"do_cancel:{room_id}"),
            InlineKeyboardButton("No, stay", callback_data="dismiss"),
        ]
    ])


def next_confirm_keyboard(room_id: str, room_name: str) -> InlineKeyboardMarkup:
    """Confirm calling the next person."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, call next", callback_data=f"do_next:{room_id}"),
            InlineKeyboardButton("No, cancel", callback_data="dismiss"),
        ]
    ])
