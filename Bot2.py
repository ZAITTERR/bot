import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "9203377526:AAEW1n6droRhhD_p1EK7e7xxMVHOkeIADcM"
CONTACT = "@Gymbrowinter"  # куда писать для покупки

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ============ КАТАЛОГ ============
# structure: (категория, пол, сезон, [(размер, цена), ...])
CATALOG = [
    {"name": "Пуховик зимний", "gender": "Мужской", "season": "Зима",
     "sizes": {"S": 7990, "M": 7990, "L": 8490, "XL": 8490}},
    {"name": "Куртка ветровка", "gender": "Мужской", "season": "Весна",
     "sizes": {"S": 3990, "M": 3990, "L": 4290, "XL": 4290}},
    {"name": "Футболка хлопок", "gender": "Мужской", "season": "Лето",
     "sizes": {"S": 990, "M": 990, "L": 1190, "XL": 1190}},
    {"name": "Платье летнее", "gender": "Женский", "season": "Лето",
     "sizes": {"S": 2490, "M": 2490, "L": 2790}},
    {"name": "Пальто демисезонное", "gender": "Женский", "season": "Осень",
     "sizes": {"S": 6490, "M": 6490, "L": 6990}},
    {"name": "Свитер шерстяной", "gender": "Женский", "season": "Зима",
     "sizes": {"S": 3490, "M": 3490, "L": 3790}},
    {"name": "Джинсы классические", "gender": "Унисекс", "season": "Любой",
     "sizes": {"S": 2990, "M": 2990, "L": 3290, "XL": 3290}},
]

GENDERS = ["Мужской", "Женский", "Унисекс"]
SEASONS = ["Зима", "Весна", "Лето", "Осень", "Любой"]
SIZES = ["S", "M", "L", "XL"]


# ============ СОСТОЯНИЯ (ШАГИ) ============
class Order(StatesGroup):
    gender = State()
    season = State()
    size = State()
    show = State()


def kb(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=o, callback_data=f"{prefix}:{o}")] for o in options]
    rows.append([InlineKeyboardButton(text="⬅️ В начало", callback_data="start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contact_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать для покупки", url=f"https://t.me/{CONTACT.lstrip('@')}")],
        [InlineKeyboardButton(text="🔍 Подобрать ещё", callback_data="start")],
    ])


# ============ ХЭНДЛЕРЫ ============
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Order.gender)
    await message.answer(
        "👋 Здравствуйте! Помогу подобрать одежду.\n\n"
        "Шаг 1 из 3 — выберите пол:",
        reply_markup=kb(GENDERS, "g"),
    )


@dp.callback_query(F.data == "start")
async def cb_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Order.gender)
    await cb.message.answer("Шаг 1 из 3 — выберите пол:", reply_markup=kb(GENDERS, "g"))
    await cb.answer()


@dp.callback_query(Order.gender, F.data.startswith("g:"))
async def cb_gender(cb: CallbackQuery, state: FSMContext):
    gender = cb.data.split(":", 1)[1]
    await state.update_data(gender=gender)
    await state.set_state(Order.season)
    await cb.message.edit_text(
        f"Пол: {gender}.\nШаг 2 из 3 — выберите сезон:",
        reply_markup=kb(SEASONS, "s"),
    )
    await cb.answer()


@dp.callback_query(Order.season, F.data.startswith("s:"))
async def cb_season(cb: CallbackQuery, state: FSMContext):
    season = cb.data.split(":", 1)[1]
    data = await state.get_data()
    await state.update_data(season=season)
    await state.set_state(Order.size)
    await cb.message.edit_text(
        f"Сезон: {season}.\nШаг 3 из 3 — выберите размер:",
        reply_markup=kb(SIZES, "z"),
    )
    await cb.answer()


@dp.callback_query(Order.size, F.data.startswith("z:"))
async def cb_size(cb: CallbackQuery, state: FSMContext):
    size = cb.data.split(":", 1)[1]
    data = await state.get_data()
    await state.set_state(Order.show)

    # фильтруем каталог
    found = [
        item for item in CATALOG
        if item["gender"] == data["gender"]
        and (item["season"] == data["season"] or item["season"] == "Любой" or data["season"] == "Любой")
        and size in item["sizes"]
    ]

    if not found:
        text = (f"😕 К сожалению, ничего не нашлось по запросу:\n"
                f"{data['gender']} • {data['season']} • размер {size}\n\n"
                f"Попробуйте другой сезон или напишите нам — подберём вручную!")
        await cb.message.edit_text(text, reply_markup=contact_kb())
    else:
        lines = ["✅ Вот что мы нашли:\n"]
        for item in found:
            lines.append(f"👚 {item['name']}")
            lines.append(f"   Сезон: {item['season']} | Размер: {size} | Цена: {item['sizes'][size]} ₽\n")
        lines.append(f"📞 Для заказа пишите: {CONTACT}")
        await cb.message.edit_text("\n".join(lines), reply_markup=contact_kb())
    await cb.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
