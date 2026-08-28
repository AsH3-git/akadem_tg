"""All user-facing strings, in Russian, in one place.

Keeping them here (instead of scattered through bot.py) means the organizer
can proofread / tweak wording without having to touch any logic.
"""

WELCOME = (
    "Привет! Это бот квеста для студентов. 🎓\n\n"
    "Чтобы получить свою последовательность обхода секторов, отправь "
    "команду /get_seq."
)

ALREADY_STARTED = (
    "Вы уже проходите квест. Если хотите начать заново, отправьте /reset."
)

SEQ_ASSIGNED = (
    "Твоя последовательность обхода секторов *{route}*! В соответствие с "
    "ней ты будешь получать координаты точек, приятного прохождения "
    "квеста, наслаждайся Академгородком!\n\n"
    "После прохождения всех секций я пришлю тебе сайт, где ты сможешь "
    "прочитать обо всех достопримечательностях, которые ты посетил!"
)

SIGHT_MESSAGE = (
    "📍 Точка {n} из {total}\n\n"
    "Координаты: `{lat}, {lon}`\n"
    "🗺 [Открыть на карте]({maps_link})\n\n"
    "Когда доберётесь до места, нажмите «Отправить фото»."
)

BTN_SEND_PHOTO = "📷 Отправить фото"
BTN_SUPPORT = "🆘 Техническая поддержка"

ASK_FOR_PHOTO = "Пришлите, пожалуйста, фото с этого места."

PHOTO_NOT_EXPECTED = (
    "Сначала нажмите «Отправить фото» под сообщением с координатами, а "
    "затем присылайте фотографию."
)

PHOTO_RECEIVED = (
    "Спасибо! Фото отправлено куратору на проверку. Ожидайте подтверждения — "
    "как только куратор проверит фото, бот пришлёт следующую точку."
)

PHOTO_APPROVED_TO_STUDENT = "✅ Место засчитано! Переходим к следующей точке."

PHOTO_REJECTED_TO_STUDENT = (
    "❌ Это фото не подходит для этого места. Пришлите, пожалуйста, другое фото."
)

# Caption sent to the manager together with the forwarded photo.
SUBMISSION_TO_MANAGER = (
    "Новое фото на проверку\n"
    "Студент: {student_name}\n"
    "Сектор: {sector}\n"
    "Точка: {sight_name}"
)

BTN_APPROVE = "✅ Подходит"
BTN_REJECT = "❌ Не подходит"

SUBMISSION_DECIDED_APPROVED = "✅ Подходит (проверено)"
SUBMISSION_DECIDED_REJECTED = "❌ Не подходит (проверено)"

NOT_YOUR_SUBMISSION = "Эта заявка закреплена за другим куратором."
ALREADY_DECIDED = "Эта заявка уже проверена."

MAIN_ROUTE_COMPLETE = (
    "Вы завершили квест, молодцы! Можете возвращаться или попробовать "
    "дойти до пары более удалённых, но не менее интересных мест."
)

BTN_FINISH = "🏁 Закончить квест"
BTN_BONUS = "🔥 Еще места для самых смелых"

# Shown at the very end of the quest, whichever way a student gets there
# (pressing "Закончить квест", or finishing the bonus sector).
FAREWELL = (
    "Возвращайся в главный корпус НГУ, там организаторы встретят тебя. Ты "
    "молодец, что не потерялся в течение квеста, не заблудись по пути в ГК!"
)

FINISH_THANKS = f"Спасибо за участие в квесте! До встречи 👋\n\n{FAREWELL}"

BTN_FULL_SITE = "🌐 Сайт с достопримечательностями"

BONUS_COMPLETE = f"Молодец!\n\n{FAREWELL}"

NEED_START = "Чтобы начать квест, отправьте /start."

YOUR_ID = "Ваш Telegram id: `{id}`"

STATS = (
    "Пользователей всего: {total}\n"
    "В процессе: {in_progress}\n"
    "Завершили квест: {finished}\n"
    "Заявок на проверке: {pending}"
)

NOT_ADMIN = "Эта команда недоступна."
