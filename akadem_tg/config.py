"""Central configuration for the quest bot.

Secrets (the bot token) come from environment variables / .env so they never
land in git. Everything else that a non-programmer organizer needs to tweak
before each event (managers, admins) lives here as plain Python so it is easy
to find and edit.
"""

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Copy .env.example to .env and put your bot "
        "token from @BotFather there."
    )

# Path to the file with sight coordinates, grouped by sector.
COORDINATES_FILE = os.path.join(os.path.dirname(__file__), "coordinates.txt")

# Path to the SQLite database file used to persist quest progress. Keeping
# state on disk (instead of only in memory) means restarting the bot doesn't
# kick every student mid-quest back to square one.
DB_PATH = os.path.join(os.path.dirname(__file__), "quest.db")

# The three sectors that make up the main route, in the order they are
# printed on students' route slips (route codes are permutations of "123").
MAIN_SECTORS = (1, 2, 3)

# The extra sector offered to students after they finish the main route.
BONUS_SECTOR = 4

# --- Managers -----------------------------------------------------------
# One manager (куратор) per sector. "id" is the manager's numeric Telegram
# user id (needed so the bot can message them, and so the bot can check that
# an "approve"/"reject" button press really comes from that manager).
# "username" is their public @handle (without the @), used for the
# "Техническая поддержка" button that links straight to their profile.
#
# HOW TO FILL THIS IN:
#   1. Each manager opens a chat with the bot and sends /start (a bot can
#      only message users who have messaged it first).
#   2. Each manager sends /id to the bot to get their numeric Telegram id.
#   3. Put that id + their @username below.
MANAGERS = {
    1: {"id": 906587490, "username": "Arseny_test", "name": "Куратор сектора 1"},
    2: {"id": 1410332479, "username": "Igor_test", "name": "Куратор сектора 2"},
    3: {"id": 1410332479, "username": "Igor_sector3", "name": "Куратор сектора 3"},
    # The bonus sector reuses sector 3's manager by default; change if needed.
    4: {"id": 1410332479, "username": "Igor_sector3", "name": "Куратор доп. точек"},
}

# Telegram user ids allowed to run the /stats admin command. Optional —
# leave empty to disable the command for everyone.
ADMIN_IDS: set[int] = set()
