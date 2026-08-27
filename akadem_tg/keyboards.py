"""Builders for every inline keyboard the bot sends."""

from itertools import permutations

from telebot import types

import texts
from config import MANAGERS

ROUTE_CODES = ["".join(p) for p in permutations("123")]


def route_selection_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton("-".join(code), callback_data=f"route:{code}")
        for code in ROUTE_CODES
    ]
    markup.add(*buttons)
    return markup


def sight_keyboard(sector: int) -> types.InlineKeyboardMarkup:
    manager = MANAGERS[sector]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(texts.BTN_SEND_PHOTO, callback_data="photo:start"))
    markup.add(
        types.InlineKeyboardButton(
            texts.BTN_SUPPORT, url=f"https://t.me/{manager['username']}"
        )
    )
    return markup


def manager_decision_keyboard(submission_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(texts.BTN_APPROVE, callback_data=f"approve:{submission_id}"),
        types.InlineKeyboardButton(texts.BTN_REJECT, callback_data=f"reject:{submission_id}"),
    )
    return markup


def finish_or_bonus_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(texts.BTN_FINISH, callback_data="finish"))
    markup.add(types.InlineKeyboardButton(texts.BTN_BONUS, callback_data="bonus"))
    return markup
