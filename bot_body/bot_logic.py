from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot_body import weather_cast, curses
import db
from dotenv import load_dotenv
import os

env_path = os.path.join('.', '.env')
load_dotenv(dotenv_path=env_path)
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', None)


bot = Bot(token=ACCESS_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
class BotStates(StatesGroup):
    weather = State() 
    curs = State()
    spent_cat = State()
    spent_sum = State()
    menu = State()


startmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
startmarkup.add('Погода', 'Курсы', 'Расходы')

@dp.message_handler(commands=['start'], state='*')
async def start(message: types.message):
    user_name = message.from_user.username
    db.create_tables(user_name)
    await BotStates.menu.set()
    await bot.send_message(
        message.from_user.id,
        'Привет, выберите сервис:',
        reply_markup=startmarkup
    )
@dp.message_handler(content_types=["text"], state=BotStates.menu)
async def handle_text(message: types.Message):
    if message.text.strip() == 'Погода':
        await BotStates.weather.set()
        await bot.send_message(message.chat.id, 'Введите город')
    elif message.text.strip() == 'Курсы':
        currency_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        currency_markup.add('USD', 'EUR')
        await BotStates.curs.set()
        await bot.send_message(message.chat.id, 'Выбор валюты:', reply_markup=currency_markup)
    elif message.text.strip() == 'Расходы':
        spent_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        spent_markup.add(*db.CATEGORIES, 'Итого', 'Назад')
        await BotStates.spent_cat.set()
        await bot.send_message(message.chat.id, 'Категория:', reply_markup=spent_markup)
    else:
        await bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

@dp.message_handler(state=BotStates.weather)
async def weather_msg(message: types.Message, state: FSMContext):
    city = message.text.strip()
    m_text = await weather_cast.get_weather(city)
    await BotStates.menu.set()
    await bot.send_message(message.chat.id, m_text)

@dp.message_handler(content_types=["text"], state=BotStates.curs)
async def currency_msg(message: types.Message, state: FSMContext):
    currency = message.text.strip()
    m_text = await curses.get_curses()
    await BotStates.menu.set()
    await bot.send_message(
        message.chat.id,
        str(m_text[currency]) + 'руб.',
        reply_markup=startmarkup
        )

@dp.message_handler(content_types=["text"], state=BotStates.spent_cat)
async def get_category(message: types.Message, state: FSMContext):
    cat = message.text.strip()
    if cat == 'Итого':
        sums = db.calculate_spent(message.from_user.username)
        m_text = ''
        for s in sums:
            m_text += f'{s[0]}: {str(s[1])}\n'
        await bot.send_message(message.chat.id, m_text)
    elif cat == 'Назад':
        await BotStates.menu.set()
        await bot.send_message(message.chat.id, 'Выберите сервис:', reply_markup=startmarkup)
    else:
        async with state.proxy() as data:
            data['cat'] = cat
        await BotStates.spent_sum.set()
        await bot.send_message(message.chat.id, 'Введите сумму:')

@dp.message_handler(content_types=["text"], state=BotStates.spent_sum)
async def add_sum(message: types.Message, state: FSMContext):
    try:
        summ = float(message.text.strip())
        async with state.proxy() as data:
            data['summ'] = summ
        db.add_spent(message.from_user.username, (data['cat'], data['summ']))
        await BotStates.menu.set()
        await bot.send_message(message.chat.id, 'Записано!', reply_markup=startmarkup)
    except ValueError:
        await BotStates.menu.set()
        await bot.send_message(message.chat.id, 'Надо число!', reply_markup=startmarkup)

