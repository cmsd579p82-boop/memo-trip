
import asyncio
from email.mime import message
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

ALLOWED_USER_IDS = {919441433, 873492075}

dp.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))
dp.callback_query.filter(F.from_user.id.in_(ALLOWED_USER_IDS))



class AddPlace(StatesGroup):
    name = State()
    city = State()
    category = State()
    budget = State()
    map_link = State()

DB_NAME = "datespot.db"



class EditPlace(StatesGroup):
    place_id = State()
    field = State()
    value = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📍 Усі місця"),
            KeyboardButton(text="🎲 Випадкове місце")
        ],
        [
            KeyboardButton(text="➕ Додати місце"),
            KeyboardButton(text="✏️ Редагувати місце")
        ],
        [
            KeyboardButton(text="💕 Результати голосування"),
            KeyboardButton(text="💸 Бюджетні побачення")
        ],
        [
            KeyboardButton(text="❓ Допомога")
        ]
    ],
    resize_keyboard=True
)

edit_keyboard = ReplyKeyboardMarkup(
    keyboard=[
            [KeyboardButton(text="Назва"),
             KeyboardButton(text="Місто")
         ],
         [
              KeyboardButton(text="Категорія"),
            KeyboardButton(text="Бюджет")
         ],
         [
             KeyboardButton(text="Посилання на карту")
         ],
         [   KeyboardButton(text="🏁 Закінчити редагування")
         ],
         [   KeyboardButton(text="❌ Скасувати")]
    ],
 
    resize_keyboard=True,
    one_time_keyboard=True
)


cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Скасувати")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

def get_vote_keyboard(place_id: int):
        return InlineKeyboardMarkup(
            inline_keyboard=[
    
        [
            InlineKeyboardButton(text="❤️ Хочу!", callback_data=f"vote_yes:{place_id}"),
            InlineKeyboardButton(text="👎 Не цього разу", callback_data=f"vote_no:{place_id}")
        ]
    ]
)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT ,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            category TEXT,
            budget TEXT,
            map_link TEXT
            )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         place_id INTEGER NOT NULL,
         user_id INTEGER NOT NULL,
         vote NOT NULL,
         UNIQUE(place_id, user_id),
         FOREIGN KEY (place_id) REFERENCES places(id)
         )
    """ )

    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привіт! 💛 Я DateSpot — ваш помічник для побачень!\n\n"
        "Я допоможу вам знаходити цікаві місця та вирішувати, "
        "куди вирушити разом.\n\n"
        "Поки що я тільки починаю працювати, але скоро тут буде "
        "набагато більше можливостей 😉",
        reply_markup=main_keyboard
    )


@dp.message(Command("add"))
@dp.message(F.text == "➕ Додати місце")
async def add_handler(message: Message, state: FSMContext):
    await state.set_state(AddPlace.name)
    await message.answer("📍 Давай додамо нове місце!\n\nЯк воно називається?",
    reply_markup=cancel_keyboard
)
    
MENU_BUTTONS = [
    "📍 Усі місця",
    "🎲 Випадкове місце",
    "➕ Додати місце",
    "✏️ Редагувати місце",
    "💕 Результати голосування",
    "💸 Бюджетні побачення",
    "❓ Допомога",
    "❌ Скасувати",
]



@dp.message(F.text == "❌ Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Дію скасовано. Нічого нового не збережено.",
        reply_markup=main_keyboard
    )



@dp.message(AddPlace.name,
            ~F.text.startswith("/"),
            ~F.text.in_(MENU_BUTTONS)
)

async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddPlace.city)
    await message.answer("🌆 У якому місті розташоване це місце?",
    reply_markup=cancel_keyboard
)
    

@dp.message(AddPlace.city,
            ~F.text.startswith("/"),
            ~F.text.in_(MENU_BUTTONS)
)

async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(AddPlace.category)
    await message.answer("🏷️ До якої категорії належить місце?",
    reply_markup=cancel_keyboard
)


@dp.message(AddPlace.category,
            ~F.text.startswith("/"),
            ~F.text.in_(MENU_BUTTONS)
)

async def process_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddPlace.budget)
    await message.answer(
        "💶 Який бюджет на одну людину в євро\n"
        "Введи суму числом, наприклад: 50 або 100.",
        reply_markup=cancel_keyboard
    ) 


@dp.message(AddPlace.budget, 
            ~F.text.startswith("/"),
            ~F.text.in_(MENU_BUTTONS)
)

async def process_budget(message: Message, state: FSMContext):
    budget_text = message.text.strip()

    if not budget_text.isdigit() or int(budget_text) <=0:
        await message.answer(
            "❌ Введи бюджет додатним цілим числом.\n"
                "Наприклад: 50 або 100.",
                reply_markup=cancel_keyboard
        )
        return

    await state.update_data(budget=int(budget_text))
    await state.set_state(AddPlace.map_link)

    await message.answer(
        "🗺️ Надішли посилання на це місце в Google Maps.",
        reply_markup=cancel_keyboard
    )

        
@dp.message(
        AddPlace.map_link,
        ~F.text.startswith("/"),
        ~F.text.in_(MENU_BUTTONS)
)

async def process_map_link(message: Message, state: FSMContext):
    await state.update_data(map_link=message.text)
    data = await state.get_data()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()


    cursor.execute(
        """INSERT INTO places (name, city, category, budget, map_link)
        VALUES (?, ?, ?, ?, ?)""",
        (
            data["name"],
            data["city"],
            data["category"],
            data["budget"],
            data["map_link"]
        )
    )

    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Місце успішно додано до DateSpot!")



@dp.message(Command("places"))
@dp.message(F.text == "📍 Усі місця")
async def places_handler(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, city, category, budget, map_link "
        "FROM places ORDER BY id"
    )
    places = cursor.fetchall()
    conn.close()

    if not places:
        await message.answer(
            "📭 Поки що місць немає. Додай перше через /add!"
        )
        return

    await message.answer("📍 Ваші місця в DateSpot:")

    for place in places:
        text = (
            f"🆔 ID: {place[0]}\n"
            f"📌 {place[1]}\n"
            f"🌆 Місто: {place[2]}\n"
            f"🏷️ Категорія: {place[3]}\n"
            f"💶 Бюджет: {place[4]} €\n"
            f"🗺️ Карта: {place[5]}"
        )

        await message.answer(
            text,
            reply_markup=get_vote_keyboard(place[0])
        )



@dp.callback_query(F.data.startswith("vote_"))
async def process_vote(callback: CallbackQuery):
    action, place_id_text = callback.data.split(":")
    place_id = int(place_id_text)

    if action == "vote_yes":
        vote = "yes"
        answer_text = "❤️ Твій голос: хочу!"
    elif action == "vote_no":
        vote = "no"
        answer_text = "👎 Твій голос: не цього разу"
    else:
        await callback.answer("❌ Невідома дія.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO votes (place_id, user_id, vote)
        VALUES (?, ?, ?)
        ON CONFLICT(place_id, user_id)
        DO UPDATE SET vote = excluded.vote
        """,
        (place_id, callback.from_user.id, vote)
    )

    conn.commit()
    conn.close()

    print(
        f"Голос: user_id={callback.from_user.id}, "
        f"place_id={place_id}, vote={vote}"
    )

    await callback.answer(answer_text)



@dp.message(Command("votes"))
@dp.message(F.text == "💕 Результати голосування")
async def votes_handler(message: Message):
    MY_ID = 919441433
    NASTYA_ID = 873492075

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            places.id,
            places.name,
            places.city,
            MAX(CASE
                WHEN votes.user_id = ? THEN votes.vote
            END),
            MAX(CASE
                WHEN votes.user_id = ? THEN votes.vote
            END)
        FROM places
        LEFT JOIN votes ON places.id = votes.place_id
        GROUP BY places.id, places.name, places.city
        ORDER BY places.id
    """, (MY_ID, NASTYA_ID))

    results = cursor.fetchall()
    conn.close()

    if not results:
        await message.answer(
            "📭 Поки що немає місць для голосування."
        )
        return

    text = "💕 Ваші збіги в DateSpot:\n\n"

    for place_id, name, city, my_vote, her_vote in results:
        if my_vote == "yes" and her_vote == "yes":
            status = "❤️ Ви обоє хочете сюди!"
        elif my_vote == "no" and her_vote == "no":
            status = "👎 Ви обоє поки не хочете сюди."
        elif my_vote is None or her_vote is None:
            status = "⏳ Чекаємо голос одного з вас."
        else:
            status = "🤝 Ваші думки поки різняться."

        my_text = {
            "yes": "❤️ Хочу",
            "no": "👎 Не цього разу",
            None: "⏳ Ще не голосував"
        }[my_vote]

        her_text = {
            "yes": "❤️ Хочу",
            "no": "👎 Не цього разу",
            None: "⏳ Ще не голосувала"
        }[her_vote]

        text += (
            f"📍 {name} — {city}\n"
            f"Твій голос: {my_text}\n"
            f"Голос Насті: {her_text}\n"
            f"Результат: {status}\n\n"
        )

    await message.answer(text)



@dp.message(Command("random"))
@dp.message(F.text == "🎲 Випадкове місце")
async def random_handler(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, city, category, budget, map_link FROM places"
    )
    places = cursor.fetchall()

    conn.close()

    if not places:
        await message.answer(
            "📭 У вашій базі ще немає місць. Додай перше через /add!"
        )
        return

    import random
    place = random.choice(places)

    await message.answer(
        f"🎲 Сьогодні DateSpot обирає за вас!\n\n"
        f"📌 {place[0]}\n"
        f"🌆 Місто: {place[1]}\n"
        f"🏷️ Категорія: {place[2]}\n"
        f"💶 Бюджет: {place[3]}\n"
        f"🗺️ Карта: {place[4]}"
    )


@dp.message(Command("cheap"))
@dp.message(F.text == "💸 Бюджетні побачення")
async def cheap_handler(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
       """SELECT name, city, category, budget, map_link
       FROM places
       WHERE CAST(budget AS REAL) <= 100
       ORDER BY CAST(budget AS REAL)""" 
    )
    places = cursor.fetchall()

    conn.close()

    if not places:
        await message.answer(
            "🤷 Не знайшов місць із бюджетом до 100€.\n"
            "Додай місце з таким бюджетом через /add!"
        )
        return

    text = "💸 Місця для бюджетного побачення:\n\n"

    for place in places:
        text += (
            f"📌 {place[0]}\n"
            f"🌆 Місто: {place[1]}\n"
            f"🏷️ Категорія: {place[2]}\n"
            f"💶 Бюджет: {place[3]}\n"
            f"🗺️ Карта: {place[4]}\n\n"
        )


    await message.answer(text)

@dp.message(Command("edit"))
@dp.message(F.text == "✏️ Редагувати місце")
async def edit_handler(message: Message, state: FSMContext):
    parts = message.text.split()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if message.text == "✏️ Редагувати місце" or len(parts) == 1:
        cursor.execute("SELECT id, name, city FROM places ORDER BY id")
        places = cursor.fetchall()
        conn.close()

        if not places:
            await message.answer(
                "📭 Поки що немає місць для редагування. "
                "Додай перше через /add!"
            )
            return

        text = "✏️ Обери місце для редагування:\n\n"

        for place in places:
            text += (
                f"🆔 ID: {place[0]}\n"
                f"📍 {place[1]}\n"
                f"🌆 {place[2]}\n\n"
            )

        text += "Введи команду /edit ID для вибору місця."

        await message.answer(text, reply_markup=main_keyboard)
        return

    if len(parts) !=2 or not parts[1].isdigit():
        conn.close()
        await message.answer(
            "✏️ Введи команду у форматі /edit ID\n"
            "Наприклад: /edit 1"

        )
        return

    place_id = int(parts[1])

    cursor.execute(
        "Select id, name, city, category, budget, map_link "
        "From places WHERE id = ?",
        (place_id,)
    )

    place = cursor.fetchone()
    conn.close()

    if place is None:
        await message.answer(
            f"🤷 Місце з ID {place_id} не знайдено."
        )
        return

    await state.update_data(place_id=place_id)
    await message.answer(
        f"✏️ Редагуємо місце №{place[0]}:\n\n"
        f"📍 Назва: {place[1]}\n"
        f"🏙️ Місто: {place[2]}\n"
        f"📂 Категорія: {place[3]}\n"
        f"💰 Бюджет: {place[4]}\n"
        f"🗺️ Карта: {place[5]}\n\n"
        "Що хочеш змінити? Натисни кнопку нижче 👇",
        reply_markup=edit_keyboard
    )

    await state.set_state(EditPlace.field)

  


@dp.message(EditPlace.field, F.text == "🏁 Закінчити редагування")
async def finish_edit_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "✅ Редагування завершено!\n\n"
        "Ось що ти можеш робити далі:\n\n"
        "/start — головне меню\n"
        "/help — список команд\n"
        "/places — усі місця\n"
        "/random — випадкове місце\n"
        "/add — додати місце\n"
        "/edit ID — редагувати місце\n"
        "/delete ID — видалити місце",
        reply_markup=ReplyKeyboardRemove()
    )



@dp.message(EditPlace.field,
            F.text != "✏️ Редагувати місце"
)
async def edit_field_handler(message: Message, state: FSMContext):
    field = message.text.strip().lower()

    allowed_fields = {
        "назва": "назву",
        "місто": "місто",
        "категорія": "категорію",
        "бюджет": "бюджет",
        "посилання на карту": "посилання на карту"
    }

    field_mapping = {
        "назва": "name",
        "місто": "city",
        "категорія": "category",
        "бюджет": "budget",
        "посилання на карту": "map_link"
    }

    if field not in allowed_fields:
        await message.answer(
            "❌ Обери одне з полів за допомогою кнопок нижче."
        )
        return

    await state.update_data(field=field_mapping[field])
    await state.set_state(EditPlace.value)

    await message.answer(
        f"✏️ Добре! Тепер напиши нове значення для поля "
        f"«{allowed_fields[field]}»."
    )


@dp.message(EditPlace.value)
async def edit_value_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    place_id = data["place_id"]
    field = data["field"]
    new_value = message.text.strip()

    if not new_value:
        await message.answer("❌ Значення не може бути порожнім.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE places SET {field} = ? WHERE id = ?",
        (new_value, place_id)
    )

    conn.commit()
    updated = cursor.rowcount
    conn.close()


    if updated == 1:
        await message.answer(
            f"✅ Місце №{place_id} успішно оновлено!\n\n"
            "Можеш змінити ще одне поле — обери кнопку 👇",
            reply_markup=edit_keyboard
    )

        await state.set_state(EditPlace.field)
    else:
        await state.clear()
        await message.answer(
            "❌ Не вдалося оновити місце."
    )


@dp.message(Command("delete"))
async def delete_handler(message: Message):
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(
            "🗑️ Щоб видалити місце, напиши:\n"
            "/delete ID\n\n"
            "Наприклад: /delete 1"
        )
        return

    place_id = int(parts[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM places WHERE id = ?",
        (place_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        await message.answer(
            f"🤷 Місце з ID {place_id} не знайдено."
        )
        return

    await message.answer(
        f"✅ Місце з ID {place_id} видалено!"
    )



@dp.message(Command("help"))
@dp.message(F.text == "❓ Допомога")
async def help_handler(message: Message):
    await message.answer(
         "Команди DateSpot 📍\n\n"
         "/start — привітання\n"
         "/help — список команд\n\n"
         "/places — переглянути всі місця\n"
         "/random — обрати випадкове місце\n"
         "/add — додати нове місце\n"
         "/edit ID — редагувати місце за ID\n"
         "/delete ID — видалити місце\n"
         "/cheap — знайти бюджетні варіанти\n"
         "/votes - переглянути результати голосування"
    )


async def main():
    init_db()

    if not TOKEN:
        raise ValueError("Не знайдено BOT_TOKEN у файлі .env")

    bot = Bot(token=TOKEN)

    print("DateSpot запущено! Натисни Ctrl+C для зупинки.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

