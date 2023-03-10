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
    spent_calc = State()
    menu = State()


startmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
startmarkup.add('Погода', 'Курсы', 'Расходы')

spent_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
spent_markup.add(*db.CATEGORIES, 'Итого', 'Назад')

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

@dp.message_handler(content_types=["text"], state=None)
async def other_text(message: types.Message):
    await bot.send_message(
        message.chat.id,
        'Бот был перезапущен, введите /start, или выберите сервис:',
        reply_markup=startmarkup
    )
    await BotStates.menu.set()

@dp.message_handler(content_types=["text"], state=BotStates.menu)
async def handle_text(message: types.Message):
    if message.text.strip() == 'Погода':
        weather_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton('Ваше местоположение', request_location=True)
        weather_markup.add(button)
        await BotStates.weather.set()
        await bot.send_message(message.chat.id, 'Введите город', reply_markup=weather_markup)
    elif message.text.strip() == 'Курсы':
        currency_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        currency_markup.add('USD', 'EUR')
        await BotStates.curs.set()
        await bot.send_message(message.chat.id, 'Выбор валюты:', reply_markup=currency_markup)
    elif message.text.strip() == 'Расходы':
        await BotStates.spent_cat.set()
        await bot.send_message(message.chat.id, 'Категория:', reply_markup=spent_markup)
    else:
        await bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

@dp.message_handler(content_types=['location', 'text'], state=BotStates.weather)
async def weather_msg(message: types.Message, state: FSMContext):
    city = ''
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
    else:
        lat, lon = None, None
        city = message.text.strip()
    m_text = await weather_cast.get_weather(city, lat=lat, lon=lon)
    await BotStates.menu.set()
    await bot.send_message(message.chat.id, m_text, reply_markup=startmarkup)

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
        month_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        month_markup.add('Предыдущий', 'Текущий')
        await BotStates.spent_calc.set()
        await bot.send_message(message.chat.id, 'Выберите месяц:', reply_markup=month_markup)
    elif cat == 'Назад':
        await BotStates.menu.set()
        await bot.send_message(message.chat.id, 'Выберите сервис:', reply_markup=startmarkup)
    else:
        async with state.proxy() as data:
            data['cat'] = cat
        await BotStates.spent_sum.set()
        await bot.send_message(message.chat.id, 'Введите сумму:')

@dp.message_handler(content_types=["text"], state=BotStates.spent_calc)
async def calculate_spent(message: types.Message, state: FSMContext):
    curr_month = (message.text.strip() == 'Текущий')
    sums = db.calculate_spent(message.from_user.username, curr_month=curr_month)
    m_text = ''
    for s in sums:
        m_text += f'{s[0]}: {str(s[1])}\n'
    await BotStates.spent_cat.set()
    await bot.send_message(message.chat.id, m_text, reply_markup=spent_markup)

@dp.message_handler(content_types=["text"], state=BotStates.spent_sum)
async def add_sum(message: types.Message, state: FSMContext):
    try:
        summ = float(message.text.strip())
        async with state.proxy() as data:
            data['summ'] = summ
        db.add_spent(message.from_user.username, (data['cat'], data['summ']))
        await BotStates.spent_cat.set()
        await bot.send_message(message.chat.id, 'Записано!', reply_markup=spent_markup)
    except ValueError:
        await BotStates.spent_cat.set()
        await bot.send_message(message.chat.id, 'Надо число!', reply_markup=spent_markup)

