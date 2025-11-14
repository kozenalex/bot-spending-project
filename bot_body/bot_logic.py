# import db
import os
from typing import Union, Set

from aiogram import Bot, Dispatcher, F
from aiogram.filters import BaseFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, message, Message
from aiogram.filters import Command, StateFilter

import weather_cast, curses
from dotenv import load_dotenv
import consts

from transmission import add_torrent_from_magnet, get_torrents, format_torrents_for_telegram

env_path = os.path.join('.', '.env')
load_dotenv(dotenv_path=env_path)


bot = Bot(token=consts.ACCESS_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States
class BotStates(StatesGroup):
    weather = State() 
    curs = State()
    # spent_cat = State()
    # spent_sum = State()
    # spent_calc = State()
    menu = State()
    transmission = State()
    add_magnet = State()

class IsAllowedUser(BaseFilter):
    def __init__(self, allowed_user_ids: Union[Set[int], list, tuple]):
        self.allowed_user_ids = set(allowed_user_ids)

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.allowed_user_ids


startmarkup = ReplyKeyboardMarkup(
    keyboard=[
        [
         KeyboardButton(text=consts.WEATHER_BUTTON),
         KeyboardButton(text=consts.RATES_BUTTON),
        #  KeyboardButton(text='Расходы'),
         KeyboardButton(text=consts.TORRENT_BUTTON)
        ]
    ], 
    resize_keyboard=True)

# spent_markup = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text=cat) for cat in db.CATEGORIES],
#         [
#             KeyboardButton(text='Итого'),
#             KeyboardButton(text=consts.BACK_COMMAND)
#         ]
#     ],
#      resize_keyboard=True)

transmission_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
         KeyboardButton(text=consts.ADD_COMMAND),
         KeyboardButton(text=consts.LIST_COMMAND),
         KeyboardButton(text=consts.BACK_COMMAND)
        ]
    ], 
    resize_keyboard=True)

@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), Command("start"), StateFilter("*"))
async def start(message: Message, state: FSMContext):
    user_name = message.from_user.username
    # db.create_tables(user_name)
    await state.set_state(BotStates.menu)
    await bot.send_message(
        message.from_user.id,
        'Привет, выберите сервис:',
        reply_markup=startmarkup
    )

@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), F.text, StateFilter(None))
async def other_text(message: Message, state: FSMContext):
    await message.answer(
        "Бот был перезапущен, введите /start, или выберите сервис:",
        reply_markup=startmarkup
    )
    await state.set_state(BotStates.menu)

@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), F.text, StateFilter(BotStates.menu))
async def handle_text(message: Message, state: FSMContext):
    text = message.text.strip()
    
    match text:
        case consts.WEATHER_BUTTON:
            weather_markup = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='Ваше местоположение', request_location=True),
                        KeyboardButton(text='Назад')
                        ]],
                resize_keyboard=True
            )
            await state.set_state(BotStates.weather)
            await message.answer('Введите город', reply_markup=weather_markup)
            
        case consts.RATES_BUTTON:
            currency_markup = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=consts.USD_BUTTON['text']),
                        KeyboardButton(text=consts.EURO_BUTTON['text']),
                        KeyboardButton(text=consts.YUAN_BUTTON['text'])
                    ]
                ],
                resize_keyboard=True
            )
            await state.set_state(BotStates.curs)
            await message.answer('Выбор валюты:', reply_markup=currency_markup)
            
        case 'Расходы':
            await state.set_state(BotStates.spent_cat)
            await message.answer('Категория:', reply_markup=spent_markup)
        
        case consts.TORRENT_BUTTON:
            await state.set_state(BotStates.transmission)
            await message.answer('Команда:', reply_markup=transmission_markup)
            
        case _:
            await message.answer(f'Вы написали: {text}')

@dp.message(F.location | F.text, StateFilter(BotStates.weather), IsAllowedUser(consts.ALLOWED_USER_IDS))
async def weather_msg(message: Message, state: FSMContext):
    city = ""
    lat = lon = None

    if message.location:
        # location — объект типа Location
        lat = message.location.latitude
        lon = message.location.longitude
    elif message.text:
        city = message.text.strip()
    elif message.text == 'Назад':
        await state.set_state(BotStates.menu)
        await message.answer('Выберите сервис:', reply_markup=startmarkup)

    m_text = await weather_cast.get_weather(city, lat=lat, lon=lon)
    
    await state.set_state(BotStates.menu)
    await message.answer(m_text, reply_markup=startmarkup)

@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), F.text, StateFilter(BotStates.curs))
async def currency_msg(message: Message, state: FSMContext):
    currency = message.text.strip()
    m_text = await curses.get_curses()
    
    match currency:
        case "$_USD":
            rate = m_text.get(consts.USD_BUTTON['code'], "—")
        case "€_EUR":
            rate = m_text.get(consts.EURO_BUTTON['code'], "—")
        case "¥_YUAN":
            rate = m_text.get(consts.YUAN_BUTTON['code'], "—")
        case _:
            rate = "-"
    await state.set_state(BotStates.menu)
    await message.answer(
        f"{rate} руб.",
        reply_markup=startmarkup
    )

@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), F.text, StateFilter(BotStates.transmission))
async def torrents_msg(message: Message, state: FSMContext):
    transmission_command = message.text.strip()
    match transmission_command:
        case 'Добавить':
            await state.set_state(BotStates.add_magnet)
            await message.answer('Введите магнет ссылку:', reply_markup=None)
        case 'Список закачек':
            try:
                torrents = await get_torrents(["id", "name", "percentDone", "status"])
                parsed_torrents = await format_torrents_for_telegram(torrents)
                for t in parsed_torrents:
                    await message.answer(t, reply_markup=transmission_markup)
            except Exception as e:
                error_answer = e
                await message.answer(error_answer, reply_markup=transmission_markup)
            await state.set_state(BotStates.transmission)                
                
        case 'Назад':
            await state.set_state(BotStates.menu)
            await message.answer('Выберите сервис:', reply_markup=startmarkup)


@dp.message(IsAllowedUser(consts.ALLOWED_USER_IDS), F.text, StateFilter(BotStates.add_magnet))
async def add_magnet_url(message: Message, state: FSMContext):

    magnet_url = message.text.strip()
    
    try: 
        answer = await add_torrent_from_magnet(magnet_url)
    except Exception as e:
        answer = e
    await state.set_state(BotStates.transmission)
    await message.answer(str(answer), ReplyKeyboardMarkup=transmission_markup)

# @dp.message(F.text, StateFilter(BotStates.spent_cat))
# async def get_category(message: Message, state: FSMContext):
#     cat = message.text.strip()
    
#     if cat == 'Итого':
#         # ✅ aiogram 3.x: клавиатура через keyboard=[]
#         month_markup = ReplyKeyboardMarkup(
#             keyboard=[
#                 [KeyboardButton(text='Предыдущий'), KeyboardButton(text='Текущий')]
#             ],
#             resize_keyboard=True
#         )
#         await state.set_state(BotStates.spent_calc)
#         await message.answer('Выберите месяц:', reply_markup=month_markup)
        
#     elif cat == 'Назад':
#         await state.set_state(BotStates.menu)
#         await message.answer('Выберите сервис:', reply_markup=startmarkup)
        
#     else:
#         # ✅ aiogram 3.x: FSMContext → data = await state.get_data(); await state.update_data(...)
#         await state.update_data(cat=cat)
#         await state.set_state(BotStates.spent_sum)
#         await message.answer('Введите сумму:')

# @dp.message(F.text, StateFilter(BotStates.spent_calc))
# async def calculate_spent(message: Message, state: FSMContext):
#     curr_month = (message.text.strip() == 'Текущий')
    
#     # Получаем username (на случай, если его нет)
#     username = message.from_user.username or str(message.from_user.id)
    
#     sums = db.calculate_spent(username, curr_month=curr_month)
    
#     # Формируем ответ (защита от пустого списка)
#     if sums:
#         m_text = "\n".join(f"{cat}: {amount}" for cat, amount in sums)
#     else:
#         m_text = "Нет данных за выбранный период."
    
#     await state.set_state(BotStates.spent_cat)
#     await message.answer(m_text, reply_markup=spent_markup)

# @dp.message(F.text, StateFilter(BotStates.spent_sum))
# async def add_sum(message: Message, state: FSMContext):
#     try:
#         summ = float(message.text.strip())
        
#         # ✅ aiogram 3.x: получаем данные из FSM
#         data = await state.get_data()
#         cat = data.get("cat")
        
#         if cat is None:
#             raise ValueError("Категория не задана")
        
#         # Сохраняем в БД
#         username = message.from_user.username or str(message.from_user.id)
#         db.add_spent(username, (cat, summ))
        
#         await state.set_state(BotStates.spent_cat)
#         await message.answer("Записано!", reply_markup=spent_markup)
        
#     except (ValueError, TypeError):
#         await state.set_state(BotStates.spent_cat)
#         await message.answer("Надо число!", reply_markup=spent_markup)

