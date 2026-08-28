"""Telegram quest bot — entry point and all handlers.

Flow in short:
  1. Student sends /start, picks a route (a permutation of sectors 1-2-3
     they were given IRL) via inline buttons.
  2. Bot sends the coordinates of the first sight in that route, with
     "Отправить фото" and "Техническая поддержка" buttons.
  3. Student presses "Отправить фото", then sends a photo. The photo is
     forwarded to the manager (куратор) responsible for the current sector,
     with "✅ Подходит" / "❌ Не подходит" buttons.
  4. The manager's decision is what advances the student: on approval the
     bot sends the next sight; on rejection it asks for another photo.
  5. After the last sight of the main route, the bot offers to stop or to
     continue into the bonus sector (Section 4 in coordinates.txt). After
     the last bonus sight it sends a final "Молодец!".

State for each student (route, current sector/sight, what we're waiting on)
is kept in SQLite (db.py) so a bot restart doesn't lose anyone's progress.
"""

import logging
import random

from telebot import types
import telebot

import config
import db
import keyboards
import texts
from coordinates import parse_coordinates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("quest_bot")

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)

# Sector number -> list of Sight(lat, lon, name), loaded once at startup.
SECTORS = parse_coordinates(config.COORDINATES_FILE)


def validate_config() -> None:
    """Fail fast at startup if coordinates.txt / config.py don't line up."""
    required_sectors = list(config.MAIN_SECTORS) + [config.BONUS_SECTOR]
    for sector in required_sectors:
        if not SECTORS.get(sector):
            raise RuntimeError(
                f"Sector {sector} has no sights in {config.COORDINATES_FILE}"
            )
        if sector not in config.MANAGERS:
            raise RuntimeError(f"Sector {sector} has no manager in config.MANAGERS")
        if config.MANAGERS[sector]["id"] < 10000:
            logger.warning(
                "Manager id for sector %s looks like a placeholder — "
                "update config.MANAGERS before going live.",
                sector,
            )


# --- helpers: figuring out "where is this student right now" -------------

def _route_list(user: "db.sqlite3.Row") -> list[int]:
    return [int(c) for c in user["route"]]


def _current_sector(user) -> int:
    if user["phase"] == db.PHASE_BONUS:
        return config.BONUS_SECTOR
    return _route_list(user)[user["sector_idx"]]


def _current_sight(user):
    return SECTORS[_current_sector(user)][user["sight_idx"]]


def _overall_position(user) -> tuple[int, int]:
    """Return (current sight number, total sights) for the progress line."""
    if user["phase"] == db.PHASE_BONUS:
        return user["sight_idx"] + 1, len(SECTORS[config.BONUS_SECTOR])
    route = _route_list(user)
    done_before = sum(len(SECTORS[s]) for s in route[: user["sector_idx"]])
    total = sum(len(SECTORS[s]) for s in route)
    return done_before + user["sight_idx"] + 1, total


def send_current_sight(chat_id: int) -> None:
    user = db.get_user(chat_id)
    sector = _current_sector(user)
    sight = _current_sight(user)
    n, total = _overall_position(user)
    maps_link = f"https://maps.google.com/?q={sight.lat},{sight.lon}"
    text = texts.SIGHT_MESSAGE.format(
        n=n, total=total, lat=sight.lat, lon=sight.lon, maps_link=maps_link
    )
    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboards.sight_keyboard(sector),
    )


def advance_after_approval(chat_id: int) -> None:
    """Called once a manager approves a photo: move the student on."""
    user = db.get_user(chat_id)

    if user["phase"] == db.PHASE_MAIN:
        route = _route_list(user)
        sector = route[user["sector_idx"]]
        sights = SECTORS[sector]
        next_sight_idx = user["sight_idx"] + 1

        if next_sight_idx < len(sights):
            db.update_user(chat_id, sight_idx=next_sight_idx, state=db.STATE_IDLE)
            send_current_sight(chat_id)
            return

        next_sector_idx = user["sector_idx"] + 1
        if next_sector_idx < len(route):
            db.update_user(chat_id, sector_idx=next_sector_idx, sight_idx=0, state=db.STATE_IDLE)
            send_current_sight(chat_id)
            return

        db.update_user(chat_id, state=db.STATE_IDLE)
        bot.send_message(chat_id, texts.MAIN_ROUTE_COMPLETE, reply_markup=keyboards.finish_or_bonus_keyboard())
        return

    # phase == bonus
    sights = SECTORS[config.BONUS_SECTOR]
    next_sight_idx = user["sight_idx"] + 1
    if next_sight_idx < len(sights):
        db.update_user(chat_id, sight_idx=next_sight_idx, state=db.STATE_IDLE)
        send_current_sight(chat_id)
        return

    db.update_user(chat_id, state=db.STATE_FINISHED)
    bot.send_message(chat_id, texts.BONUS_COMPLETE)


# --- student-facing commands ----------------------------------------------

@bot.message_handler(commands=["start"])
def handle_start(message: types.Message) -> None:
    chat_id = message.chat.id
    db.create_user(chat_id, message.from_user.username, message.from_user.full_name)
    user = db.get_user(chat_id)
    if user["route"]:
        bot.send_message(chat_id, texts.ALREADY_STARTED)
        return
    bot.send_message(chat_id, texts.WELCOME)


@bot.message_handler(commands=["reset"])
def handle_reset(message: types.Message) -> None:
    chat_id = message.chat.id
    db.reset_user(chat_id)
    bot.send_message(chat_id, texts.WELCOME)


@bot.message_handler(commands=["get_seq"])
def handle_get_seq(message: types.Message) -> None:
    chat_id = message.chat.id
    user = db.get_user(chat_id)
    if user is None:
        bot.send_message(chat_id, texts.NEED_START)
        return
    if user["route"]:
        bot.send_message(chat_id, texts.ALREADY_STARTED)
        return

    route = random.choice(keyboards.ROUTE_CODES)
    db.update_user(chat_id, route=route, phase=db.PHASE_MAIN, sector_idx=0, sight_idx=0, state=db.STATE_IDLE)
    bot.send_message(chat_id, texts.SEQ_ASSIGNED.format(route="-".join(route)), parse_mode="Markdown")
    send_current_sight(chat_id)


@bot.message_handler(commands=["id"])
def handle_id(message: types.Message) -> None:
    bot.send_message(message.chat.id, texts.YOUR_ID.format(id=message.from_user.id), parse_mode="Markdown")


@bot.message_handler(commands=["stats"])
def handle_stats(message: types.Message) -> None:
    if message.from_user.id not in config.ADMIN_IDS:
        bot.send_message(message.chat.id, texts.NOT_ADMIN)
        return
    counts = db.count_users_by_state()
    total = sum(counts.values())
    finished = counts.get(db.STATE_FINISHED, 0)
    bot.send_message(
        message.chat.id,
        texts.STATS.format(
            total=total,
            in_progress=total - finished,
            finished=finished,
            pending=db.count_pending_submissions(),
        ),
    )


@bot.callback_query_handler(func=lambda call: call.data == "photo:start")
def handle_photo_start(call: types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    user = db.get_user(chat_id)
    if user is None or user["state"] != db.STATE_IDLE:
        bot.answer_callback_query(call.id)
        return
    db.update_user(chat_id, state=db.STATE_AWAITING_PHOTO)
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, texts.ASK_FOR_PHOTO)


@bot.message_handler(content_types=["photo"])
def handle_photo(message: types.Message) -> None:
    chat_id = message.chat.id
    user = db.get_user(chat_id)
    if user is None or user["state"] != db.STATE_AWAITING_PHOTO:
        bot.send_message(chat_id, texts.PHOTO_NOT_EXPECTED)
        return

    sector = _current_sector(user)
    sight = _current_sight(user)
    file_id = message.photo[-1].file_id  # largest resolution

    submission_id = db.create_submission(chat_id, sector, sight.name, file_id)
    db.update_user(chat_id, state=db.STATE_AWAITING_APPROVAL)

    manager = config.MANAGERS[sector]
    student_name = message.from_user.full_name or (
        f"@{message.from_user.username}" if message.from_user.username else str(chat_id)
    )
    caption = texts.SUBMISSION_TO_MANAGER.format(
        student_name=student_name, sector=sector, sight_name=sight.name
    )
    sent = bot.send_photo(
        manager["id"], file_id, caption=caption,
        reply_markup=keyboards.manager_decision_keyboard(submission_id),
    )
    db.set_submission_manager_message(submission_id, manager["id"], sent.chat.id, sent.message_id)
    logger.info("submission %s created: chat=%s sector=%s", submission_id, chat_id, sector)

    bot.send_message(chat_id, texts.PHOTO_RECEIVED)


# --- manager-facing --------------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve:") or call.data.startswith("reject:"))
def handle_manager_decision(call: types.CallbackQuery) -> None:
    action, submission_id_str = call.data.split(":", 1)
    submission_id = int(submission_id_str)
    submission = db.get_submission(submission_id)

    if submission is None:
        bot.answer_callback_query(call.id)
        return
    if submission["manager_id"] != call.from_user.id:
        bot.answer_callback_query(call.id, texts.NOT_YOUR_SUBMISSION, show_alert=True)
        return
    if submission["status"] != db.SUBMISSION_PENDING:
        bot.answer_callback_query(call.id, texts.ALREADY_DECIDED, show_alert=True)
        return

    student_chat_id = submission["chat_id"]
    bot.edit_message_reply_markup(
        chat_id=submission["manager_chat_id"],
        message_id=submission["manager_message_id"],
        reply_markup=None,
    )

    if action == "approve":
        db.decide_submission(submission_id, db.SUBMISSION_APPROVED)
        bot.answer_callback_query(call.id, texts.SUBMISSION_DECIDED_APPROVED)
        bot.send_message(student_chat_id, texts.PHOTO_APPROVED_TO_STUDENT)
        logger.info("submission %s approved by %s", submission_id, call.from_user.id)
        advance_after_approval(student_chat_id)
    else:
        db.decide_submission(submission_id, db.SUBMISSION_REJECTED)
        bot.answer_callback_query(call.id, texts.SUBMISSION_DECIDED_REJECTED)
        db.update_user(student_chat_id, state=db.STATE_AWAITING_PHOTO)
        bot.send_message(student_chat_id, texts.PHOTO_REJECTED_TO_STUDENT)
        logger.info("submission %s rejected by %s", submission_id, call.from_user.id)


# --- post-main-route choices ------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data == "finish")
def handle_finish(call: types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    db.update_user(chat_id, state=db.STATE_FINISHED)
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, texts.FINISH_THANKS, reply_markup=keyboards.final_site_keyboard(config.SITE_URL))


@bot.callback_query_handler(func=lambda call: call.data == "bonus")
def handle_bonus(call: types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    db.update_user(chat_id, phase=db.PHASE_BONUS, sight_idx=0, state=db.STATE_IDLE)
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    send_current_sight(chat_id)


# --- fallback for anything else --------------------------------------------

@bot.message_handler(func=lambda m: not (m.text and m.text.startswith("/")), content_types=["text"])
def handle_fallback_text(message: types.Message) -> None:
    chat_id = message.chat.id
    user = db.get_user(chat_id)
    if user is None or not user["route"]:
        bot.send_message(chat_id, texts.NEED_START)
    elif user["state"] == db.STATE_AWAITING_PHOTO:
        bot.send_message(chat_id, texts.ASK_FOR_PHOTO)


if __name__ == "__main__":
    db.init_db()
    validate_config()
    logger.info("Quest bot starting (polling)...")
    bot.infinity_polling(skip_pending=True, timeout=60)
